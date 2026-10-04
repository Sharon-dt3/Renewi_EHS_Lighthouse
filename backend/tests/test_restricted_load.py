import io, pickle, zipfile
import pytest, torch
from scripts import restricted_load as rl

def make_zip(path, payload: bytes):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("m/data.pkl", payload); z.writestr("m/byteorder", "little")

class Evil:                      # unpickling would call os.system
    def __reduce__(self):
        import os
        return (os.system, ("echo pwned > /tmp/should_not_exist_ppe5",))

def test_benign_tensor_checkpoint_loads(tmp_path):
    p = tmp_path / "ok.pt"; torch.save({"w": torch.ones(2, 2), "meta": {"epoch": 3}}, p)
    out = rl.load_restricted(p)
    assert torch.equal(out["w"], torch.ones(2, 2)) and out["meta"]["epoch"] == 3

def test_malicious_pickle_is_refused_before_anything_runs(tmp_path):
    p = tmp_path / "evil.pt"; make_zip(p, pickle.dumps({"x": Evil()}, protocol=2))
    with pytest.raises(rl.UnsafeCheckpoint): rl.load_restricted(p)
    import os; assert not os.path.exists("/tmp/should_not_exist_ppe5")

@pytest.mark.parametrize("name", ["os.system", "posix.system", "subprocess.Popen", "builtins.eval", "builtins.exec",
                                   "builtins.getattr", "sys.modules", "shutil.rmtree", "socket.socket", "torch.load", "numpy.load"])
def test_dangerous_or_unknown_globals_not_allowed(name):
    assert not rl.is_allowed(name)

@pytest.mark.parametrize("name", ["collections.OrderedDict", "torch._utils._rebuild_tensor_v2", "torch.nn.modules.conv.Conv2d",
                                   "ultralytics.nn.modules.block.C2f", "ultralytics.nn.tasks.DetectionModel", "__builtin__.set"])
def test_expected_globals_allowed(name):
    assert rl.is_allowed(name)

def test_prefix_cannot_smuggle_denied_fragment():
    assert not rl.is_allowed("torch.nn.modules.os.system")

def test_missing_or_multiple_pickles_refused(tmp_path):
    p = tmp_path / "none.pt"
    with zipfile.ZipFile(p, "w") as z: z.writestr("m/other", "x")
    with pytest.raises(rl.UnsafeCheckpoint): rl.scan_globals(p)

def test_pick_model_prefers_ema_and_refuses_empty():
    class M(torch.nn.Module):
        def forward(self, x): return x
    ema, mod = M(), M()
    assert rl.pick_model({"ema": ema, "model": mod}) is ema
    assert rl.pick_model({"ema": None, "model": mod}) is mod
    with pytest.raises(rl.UnsafeCheckpoint): rl.pick_model({"ema": None, "model": None})
