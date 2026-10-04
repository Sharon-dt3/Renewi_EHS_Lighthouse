"""Synthetic S12 integration regressions; these are not approved VAL-04 fixtures."""
import json
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from ppe.analysis import FrameAnalyzer, to_dict
from ppe.class_map import ClassMap
from ppe.detector import Detector
from ppe.yolo_detector import YoloDetector
from ppe.zone import Polygon, ZoneIncursionDetector
from ppe.zone_config import ZoneConfigError, load_zone
from scripts import run_incidents, run_inference

CMAP = ClassMap("synthetic", "test", {
    0: "person", 1: "helmet", 2: "no_helmet", 3: "safety_vest", 4: "no_safety_vest",
})
FRAME = np.zeros((1080, 1920, 3), np.uint8)
ZONE = Polygon(((900, 800), (1100, 800), (1100, 1080), (900, 1080)), (1920, 1080))


# PUBLIC_INTERFACE
class StubDetector(Detector):
    """Return synthetic source-coordinate detections and count invocations."""

    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    # PUBLIC_INTERFACE
    def detect(self, frame):
        """Return a copy of configured detections for the source frame."""
        self.calls += 1
        return list(self.raw)


@pytest.mark.parametrize("vertices", [
    ((0, 0), (1, 1)),
    ((0, 0), (1, 1), (2, 2)),
    ((0, 0), (10, 0), (10, 10), (0, 0)),
    ((0, 0), (float("nan"), 0), (0, 10)),
    ((0, 0), (float("inf"), 0), (0, 10)),
    ((0, 0), (4, 4), (0, 4), (4, 0)),
    ((0, 0), (6, 0), (3, 0), (3, 4), (0, 4)),  # adjacent overlap
    ((0, 0), (6, 0), (6, 6), (3, 0), (0, 6)),  # non-adjacent touch
])
def test_invalid_geometry_rejected(vertices):
    with pytest.raises(ValueError):
        Polygon(vertices)


@pytest.mark.parametrize("vertices", [
    ((0, 0), (5, 0), (10, 0), (10, 10), (0, 10)),
    ((0, 10), (10, 10), (10, 0), (0, 0)),
    ((0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)),
])
def test_valid_collinear_clockwise_and_concave_polygons(vertices):
    assert Polygon(vertices).contains((2, 2))


@pytest.mark.parametrize("body", [
    "[]", "clips: []", "clips: {clip: []}", "clips: {clip: {polygon: null}}",
    "clips: {clip: {polygon: [[0,0], [.nan,0], [0,10]]}}",
    "clips: {clip: {polygon: [[0,0], [10,0], [0,10]], source_size: [0,1080]}}",
    "clips: {clip: {polygon: [[0,0], [10,0], [0,10]], source_size: [1920.5,1080]}}",
    "clips: {clip: {polygon: [[0,0], [10,0], [0,10]], source_size: wrong}}",
    "clips: [",
])
def test_malformed_zone_yaml_has_domain_error(tmp_path, body):
    config = tmp_path / "zones.yaml"
    config.write_text(body)
    with pytest.raises(ZoneConfigError):
        load_zone(config, "clip")


@pytest.mark.parametrize("x,y,expected", [
    (1000, 900, True),       # inside
    (1000, 800, True),       # horizontal boundary
    (900, 900, True),        # vertical boundary
    (900, 800, True),        # corner
    (899.999, 900, False),   # just outside, no rounding
    (1000, 799.999, False),
])
def test_source_pixels_bottom_centre_and_boundary(x, y, expected):
    detector = StubDetector([(0, .95, x - 50, 200, x + 50, y)])
    result = FrameAnalyzer(detector, CMAP, zone_detector=ZoneIncursionDetector(ZONE)).analyze("f", FRAME, 0)
    data = to_dict(result)
    assert (data["width"], data["height"]) == (1920, 1080)
    assert data["people"][0]["foot_point"] == [x, y]
    assert data["people"][0]["zone_incursion"] is expected
    assert bool(result.events) is expected
    assert detector.calls == 1


def test_box_overlap_is_not_foot_point_incursion():
    detector = StubDetector([(0, .95, 850, 700, 1150, 790)])
    result = FrameAnalyzer(detector, CMAP, zone_detector=ZoneIncursionDetector(ZONE)).analyze("f", FRAME)
    assert result.events == ()  # feet above zone despite horizontal overlap


def test_combined_event_belongs_only_to_same_person():
    raw = [
        (0, .95, 950, 200, 1050, 900),
        (2, .9, 970, 220, 1030, 300),
        (3, .9, 970, 400, 1030, 500),
        (0, .95, 100, 200, 200, 900),
        (1, .9, 120, 220, 180, 300),
        (4, .9, 120, 400, 180, 500),
    ]
    analyzer = FrameAnalyzer(StubDetector(raw), CMAP, zone_detector=ZoneIncursionDetector(ZONE))
    data = to_dict(analyzer.analyze("f", FRAME))
    outside, inside = data["people"]  # stable spatial order, not raw model order
    assert outside["rules"] == ["PPE_VEST_MISSING"]
    assert outside["zone_incursion"] is False
    assert inside["state"] == "HELMET_MISSING"
    assert inside["rules"] == ["PPE_HELMET_MISSING", "ZONE_INCURSION"]
    assert data["events"][1]["person_index"] == inside["index"]
    analyzer = FrameAnalyzer(StubDetector(list(reversed(raw))), CMAP,
                             zone_detector=ZoneIncursionDetector(ZONE))
    reordered = to_dict(analyzer.analyze("f", FRAME))
    assert reordered["people"] == data["people"]
    assert reordered["events"] == data["events"]


@pytest.mark.parametrize("ppe,state,rules", [
    ([(1, .9, 970, 220, 1030, 300), (3, .9, 970, 400, 1030, 500)],
     "COMPLIANT", ["ZONE_INCURSION"]),
    ([], "UNKNOWN", ["ZONE_INCURSION"]),
    ([(2, .9, 970, 220, 1030, 300), (4, .9, 970, 400, 1030, 500)],
     "HELMET_AND_VEST_MISSING", ["PPE_HELMET_MISSING", "PPE_VEST_MISSING", "ZONE_INCURSION"]),
    ([(1, .9, 970, 220, 1030, 300), (2, .9, 970, 220, 1030, 300),
      (3, .9, 970, 400, 1030, 500)], "UNKNOWN", ["ZONE_INCURSION"]),
])
def test_zone_event_preserves_s11_states(ppe, state, rules):
    raw = [(0, .95, 950, 200, 1050, 900)] + ppe
    data = to_dict(FrameAnalyzer(StubDetector(raw), CMAP, zone_detector=ZoneIncursionDetector(ZONE))
                   .analyze("f", FRAME, 0))
    assert data["events"][0]["state"] == state
    assert data["events"][0]["rules"] == rules


@pytest.mark.parametrize("zone,frame", [
    (ZONE, np.zeros((640, 640, 3), np.uint8)),
    (Polygon(((0, 0), (2000, 0), (0, 100))), FRAME),
    (Polygon(((-1, 0), (10, 0), (0, 100))), FRAME),
    (ZONE, object()),
])
def test_wrong_frame_rejected_before_detection(zone, frame):
    detector = StubDetector([])
    analyzer = FrameAnalyzer(detector, CMAP, zone_detector=ZoneIncursionDetector(zone))
    with pytest.raises(ValueError):
        analyzer.analyze("f", frame)
    assert detector.calls == 0


def test_yolo_adapter_keeps_original_pixels_at_different_imgsz():
    class Tensor:
        def __init__(self, values):
            self.values = np.array(values)

        def cpu(self):
            return self

        def numpy(self):
            return self.values

    seen = []

    def predict(frame, **kwargs):
        seen.append((frame.shape, kwargs["imgsz"]))
        boxes = SimpleNamespace(xyxy=Tensor([[950, 200, 1050, 800]]),
                                conf=Tensor([.95]), cls=Tensor([0]))
        return [SimpleNamespace(boxes=boxes)]

    adapter = YoloDetector(SimpleNamespace(predict=predict), imgsz=640)
    result = FrameAnalyzer(adapter, CMAP, zone_detector=ZoneIncursionDetector(ZONE)).analyze("f", FRAME)
    assert seen == [((1080, 1920, 3), 640)]
    assert to_dict(result)["events"][0]["foot_point"] == [1000, 800]


@pytest.mark.parametrize("runner", ["inference", "incidents"])
def test_cli_decodes_video_and_emits_immediate_combined_event(tmp_path, monkeypatch, runner):
    from ppe import yolo_detector

    video = tmp_path / "synthetic.mp4"
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"mp4v"), 4, (320, 240))
    assert writer.isOpened()
    for _ in range(3):  # less than the 1.5-second sustained hold
        writer.write(np.zeros((240, 320, 3), np.uint8))
    writer.release()
    zones = tmp_path / "zones.yaml"
    zones.write_text("clips:\n  synthetic:\n    source_size: [320, 240]\n"
                     "    polygon: [[100,200], [220,200], [220,240], [100,240]]\n")
    detector = StubDetector([
        (0, .95, 120, 20, 200, 200),  # bottom-centre exactly on boundary
        (2, .9, 140, 30, 180, 60),
        (3, .9, 140, 90, 180, 150),
    ])
    monkeypatch.setattr(yolo_detector, "load_yolo_detector", lambda *args: (detector, CMAP))
    output = tmp_path / "output"
    common = ["--checkpoint", str(tmp_path / "unused.pt"), "--out", str(output), "--zones", str(zones)]
    if runner == "inference":
        assert run_inference.main(common + ["--input", str(video), "--every-seconds", ".25"]) == 0
        data = json.loads((output / "detections.json").read_text())
        observations = [item["analysis"] for item in data["items"]]
    else:
        assert run_incidents.main(common + ["--video", str(video)]) == 0
        data = json.loads((output / "incidents.json").read_text())
        assert data["incidents"] == []  # immediate observations are not delayed incidents
        observations = data["timeline"]
    assert len(observations) == 3 and detector.calls == 3
    for frame in observations:
        assert (frame["width"], frame["height"]) == (320, 240)
        assert frame["events"][0]["foot_point"] == [160, 200]
        assert frame["events"][0]["state"] == "HELMET_MISSING"
        assert frame["events"][0]["rules"] == ["PPE_HELMET_MISSING", "ZONE_INCURSION"]


@pytest.mark.parametrize("runner", [run_inference, run_incidents])
def test_unknown_clip_refused_before_checkpoint_loading(tmp_path, monkeypatch, runner):
    from ppe import yolo_detector

    zones = tmp_path / "zones.yaml"
    zones.write_text("clips: {}")
    called = []
    monkeypatch.setattr(yolo_detector, "load_yolo_detector", lambda *args: called.append(args))
    input_arg = "--input" if runner is run_inference else "--video"
    with pytest.raises(SystemExit, match="No zone for clip"):          # one clear line, not a traceback
        runner.main(["--checkpoint", "unused.pt", input_arg, "unknown.mp4",
                     "--out", str(tmp_path / "out"), "--zones", str(zones)])
    assert called == []


@pytest.mark.parametrize("runner", [run_inference, run_incidents])
def test_clip_id_requires_zone_config(runner):
    input_arg = "--input" if runner is run_inference else "--video"
    with pytest.raises(SystemExit) as error:
        runner.main(["--checkpoint", "unused.pt", input_arg, "clip.mp4",
                     "--out", "unused", "--clip-id", "clip"])
    assert error.value.code == 2


def test_bow_tie_polygon_is_reported_as_self_intersecting_not_zero_area():
    with pytest.raises(ValueError, match="self-intersect"):
        Polygon(((0, 0), (1000, 1000), (1000, 0), (0, 1000)))           # signed area cancels to zero


def test_collinear_polygon_is_still_reported_as_zero_area():
    with pytest.raises(ValueError, match="non-zero area"):
        Polygon(((0, 0), (1, 1), (2, 2)))


def _write_zone(path, size, name="clip"):
    path.write_text(f"clips:\n  {name}:\n    source_size: {list(size)}\n    polygon: [[10, 10], [60, 10], [60, 40], [10, 40]]\n")


def test_zone_resolution_mismatch_exits_with_one_clear_line_before_any_model(tmp_path):
    import numpy as np, cv2
    from scripts import run_inference as ri
    img = tmp_path / "clip.png"; cv2.imwrite(str(img), np.zeros((48, 64, 3), np.uint8))      # 64x48 source
    cfg = tmp_path / "zones.yaml"; _write_zone(cfg, (1920, 1080))
    with pytest.raises(SystemExit) as e:
        ri.load_zone_for_source(cfg, "clip", img)
    msg = str(e.value)
    assert "\n" not in msg and "does not match frame (64, 48)" in msg and "clip" in msg


def test_matching_zone_loads_and_unknown_or_malformed_zones_exit_cleanly(tmp_path):
    import numpy as np, cv2
    from scripts import run_inference as ri
    img = tmp_path / "clip.png"; cv2.imwrite(str(img), np.zeros((48, 64, 3), np.uint8))
    cfg = tmp_path / "zones.yaml"; _write_zone(cfg, (64, 48))
    assert ri.load_zone_for_source(cfg, "clip", img) is not None
    with pytest.raises(SystemExit):
        ri.load_zone_for_source(cfg, "no_such_clip", img)
    with pytest.raises(SystemExit):
        ri.load_zone_for_source(cfg, "clip", tmp_path / "missing.png")                       # unreadable source
