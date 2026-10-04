#!/usr/bin/env python3
"""Leakage-aware re-split of CSS v27 by SOURCE PHOTO (read-only on the dataset).

Writes only reports/split/{split_manifest.csv,summary.json,links.csv,verify_top.csv}.

Design (v2 - no transitive chaining; the first version chained false matches into
one giant group):
 1. Group files by Roboflow source name, then merge near-duplicates (dHash).
 2. Pick a pool of candidate held-out groups (single source family, has target classes).
 3. Test every candidate against EVERY other group representative with ORB+RANSAC
    (also against a horizontally flipped copy; training images are 4-tile mosaics so
    a plain photo can hide as a tile). A candidate with any strong match is
    disqualified from held-out and simply stays in train. No merging.
 4. From surviving candidates, stratify ~100 groups to valid and ~100 to test,
    ONE image per group. Other copies of a held-out photo are excluded (never trained).
 5. Verify with a DIFFERENT detector (SIFT): every held-out image vs every train
    group representative; list the top-scoring pairs for human spot-checking.

Usage: .venv/bin/python utils/build_group_split.py [--seed 0]
"""
import argparse, collections, csv, json, multiprocessing as mp, random, re, sys
from pathlib import Path
import cv2
import numpy as np
cv2.setNumThreads(0)          # OpenCV threads + fork deadlock on macOS
cv2.ocl.setUseOpenCL(False)

def _find_root():
    for p in Path(__file__).resolve().parents:
        if (p / "raw_css_dataset").is_dir():
            return p
    raise SystemExit("raw_css_dataset/ not found in any parent directory")
ROOT = _find_root()
DS = ROOT / "raw_css_dataset" / "Construction Site Safety.v27-yolov8.yolov8"
OUT = ROOT / "reports" / "split"
FAM_RE = re.compile(r"^(?P<fam>.+?)[._]rf[._][0-9a-f]{32}$")
NAMES = ['Hardhat','Mask','NO-Hardhat','NO-Mask','NO-Safety Vest','Person','Safety Cone','Safety Vest','machinery','vehicle']
TARGET = {"Person","Hardhat","NO-Hardhat","Safety Vest","NO-Safety Vest"}
HAM_DUP = 5          # dHash bits (of 64) for near-duplicate
ORB_MIN = 50         # RANSAC inliers; random cross pairs peaked at 47 in a 300-pair probe
SIFT_MIN = 30        # verification threshold (reported, plus top pairs for eyeballing)
VAL_GROUPS, TEST_GROUPS, POOL = 100, 100, 270

def _gray(path, flip=False):
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    return cv2.flip(g, 1) if flip else g

def _desc(det, path, flip=False):
    kp, d = det.detectAndCompute(_gray(path, flip), None)
    return (np.float32([k.pt for k in kp]) if kp else np.zeros((0, 2), np.float32)), d

def _inl(a, b, norm):
    (pa, da), (pb, db) = a, b
    if da is None or db is None or len(da) < 8 or len(db) < 8: return 0
    m = cv2.BFMatcher(norm).knnMatch(da, db, k=2)
    good = [x[0] for x in m if len(x) == 2 and x[0].distance < 0.75 * x[1].distance]
    if len(good) < 10: return 0
    src = pa[[g.queryIdx for g in good]].reshape(-1, 1, 2); dst = pb[[g.trainIdx for g in good]].reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
    return int(mask.sum()) if mask is not None else 0

def dhash(path):
    g = cv2.resize(_gray(path), (9, 8), interpolation=cv2.INTER_AREA)
    return np.packbits((g[:, 1:] > g[:, :-1]).flatten()).view(np.uint64)[0]

def read_labels(split, stem):
    c = collections.Counter(); f = DS / split / "labels" / f"{stem}.txt"
    if f.exists():
        for l in f.read_text().splitlines():
            if l.strip(): c[NAMES[int(l.split()[0])]] += 1
    return c

S = {}                                   # fork-shared worker state
def _orb_pair(ij):
    i, j = ij
    return i, j, max(_inl(S["od"][i], S["od"][j], cv2.NORM_HAMMING), _inl(S["od"][i], S["of"][j], cv2.NORM_HAMMING))
def _sift_pair(ij):
    i, j = ij
    return i, j, max(_inl(S["sd"][i], S["sd"][j], cv2.NORM_L2), _inl(S["sd"][i], S["sf"][j], cv2.NORM_L2))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=0)
    seed = ap.parse_args().seed; rng = random.Random(seed)
    OUT.mkdir(parents=True, exist_ok=True)

    imgs = []
    for split in ("train", "valid", "test"):
        for p in sorted((DS / split / "images").iterdir()):
            if p.name.startswith("._") or p.suffix.lower() not in {".jpg", ".jpeg", ".png"}: continue
            m = FAM_RE.match(p.stem)
            imgs.append(dict(path=p, split=split, name=p.name, stem=p.stem, fam=m.group("fam") if m else p.stem))
    n = len(imgs); print(f"{n} images", flush=True)

    par = list(range(n))
    def find(x):
        while par[x] != x: par[x] = par[par[x]]; x = par[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: par[b] = a
    byfam = collections.defaultdict(list)
    for i, im in enumerate(imgs): byfam[im["fam"]].append(i)
    for idx in byfam.values():
        for j in idx[1:]: union(idx[0], j)
    h = np.array([dhash(im["path"]) for im in imgs], dtype=np.uint64)
    dup = 0
    for i in range(n):
        bits = np.unpackbits((h[i + 1:] ^ h[i]).view(np.uint8).reshape(-1, 8), axis=1).sum(1)
        for k in np.nonzero(bits <= HAM_DUP)[0]:
            if find(i) != find(i + 1 + k): union(i, i + 1 + k); dup += 1
    comp = collections.defaultdict(list)
    for i in range(n): comp[find(i)].append(i)
    fam_n = {g: len({imgs[i]['fam'] for i in v}) for g, v in comp.items()}
    print(f"{len(comp)} groups after filename+dHash ({dup} dHash merges); largest {sorted(map(len, comp.values()), reverse=True)[:5]}", flush=True)

    def eval_img(v): return sorted(v, key=lambda i: imgs[i]["name"])[0]
    counts = {g: read_labels(imgs[eval_img(v)]["split"], imgs[eval_img(v)]["stem"]) for g, v in comp.items()}
    elig = [g for g in comp if fam_n[g] == 1 and sum(counts[g][c] for c in TARGET) > 0]
    rng.shuffle(elig)
    # pool biased to rare target classes so held-out keeps NO-Safety Vest / Hardhat examples
    tot = collections.Counter(c for g in elig for c in TARGET if counts[g][c])
    elig.sort(key=lambda g: min((tot[c] for c in TARGET if counts[g][c]), default=1e9))
    pool = elig[:POOL]
    print(f"{len(elig)} eligible groups, pool {len(pool)}", flush=True)

    # ---- step 3: ORB candidate-vs-everything (reps), disqualify on any match ----
    orb = cv2.ORB_create(nfeatures=1000, fastThreshold=10)
    S["od"] = {g: _desc(orb, imgs[eval_img(comp[g])]["path"]) for g in comp}
    S["of"] = {g: _desc(orb, imgs[eval_img(comp[g])]["path"], True) for g in comp}
    pairs = [(c, g) for c in pool for g in comp if g != c]
    print(f"ORB candidate matching: {len(pairs)} pairs", flush=True)
    links = []
    with mp.get_context("fork").Pool(mp.cpu_count()) as p:
        for k, (i, j, s) in enumerate(p.imap_unordered(_orb_pair, pairs, chunksize=500)):
            if s >= ORB_MIN: links.append(("orb", i, j, s))
            if k % 20000 == 0: print(f"  {k}/{len(pairs)}", flush=True)
    bad = {i for _, i, _, _ in links}
    survivors = [g for g in pool if g not in bad]
    print(f"{len(bad)} candidates disqualified by region matches; {len(survivors)} survive", flush=True)

    # ---- step 4: stratified assignment of survivors ----
    want = {"valid": VAL_GROUPS, "test": TEST_GROUPS}
    got = {"valid": [], "test": []}; have = {s: collections.Counter() for s in want}
    stot = collections.Counter(c for g in survivors for c in TARGET for _ in range(counts[g][c]))
    share = {s: want[s] / max(len(survivors), 1) for s in want}
    for g in survivors:
        best, bs = None, -1e9
        for s in want:
            if len(got[s]) >= want[s]: continue
            sc = sum((stot[c] * share[s] - have[s][c]) / max(stot[c], 1) for c in TARGET if counts[g][c])
            if sc > bs: best, bs = s, sc
        if best is None: break
        got[best].append(g)
        for c in TARGET: have[best][c] += counts[g][c]
    held = {g: s for s in got for g in got[s]}

    rows, per = [], collections.defaultdict(collections.Counter)
    for g, v in comp.items():
        e = eval_img(v)
        for i in v:
            im = imgs[i]
            if g in held:
                role, ns, why = ("eval", held[g], "one image per source group") if i == e else ("excluded", "none", "other copy of a held-out source (never train)")
            else:
                role, ns, why = "train", "train", ""
            rows.append([im["name"], im["split"], ns, role, im["fam"], f"G{g:04d}", len(v), fam_n[g], why])
            if role in ("train", "eval"):
                for c, k in read_labels(im["split"], im["stem"]).items(): per[ns][c] += k
    with open(OUT / "split_manifest.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["image", "old_split", "new_split", "role", "source_family", "group", "files_in_group", "families_in_group", "note"]); w.writerows(sorted(rows))
    with open(OUT / "links.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["method", "candidate", "other", "score"])
        for r, i, j, s in links: w.writerow([r, imgs[eval_img(comp[i])]["name"], imgs[eval_img(comp[j])]["name"], s])

    # ---- step 5: independent verification with SIFT ----
    ev = [g for g in held]; trn = [g for g in comp if g not in held]
    sift = cv2.SIFT_create(nfeatures=800)
    S["sd"] = {g: _desc(sift, imgs[eval_img(comp[g])]["path"]) for g in ev + trn}
    S["sf"] = {g: _desc(sift, imgs[eval_img(comp[g])]["path"], True) for g in ev + trn}
    vp = [(a, b) for a in ev for b in trn]
    print(f"SIFT verification: {len(vp)} held-out-vs-train pairs", flush=True)
    scores = []
    with mp.get_context("fork").Pool(mp.cpu_count()) as p:
        for k, (i, j, s) in enumerate(p.imap_unordered(_sift_pair, vp, chunksize=200)):
            scores.append((s, i, j))
            if k % 20000 == 0: print(f"  verify {k}/{len(vp)}", flush=True)
    scores.sort(reverse=True)
    with open(OUT / "verify_top.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["sift_inliers", "heldout_image", "heldout_split", "train_image"])
        for s, i, j in scores[:40]:
            w.writerow([s, imgs[eval_img(comp[i])]["name"], held[i], imgs[eval_img(comp[j])]["name"]])
    fam_leak = {imgs[i]["fam"] for g in ev for i in comp[g]} & {imgs[i]["fam"] for g in trn for i in comp[g]}

    summ = dict(
        seed=seed, images=n, groups=len(comp),
        pool=len(pool), disqualified_by_orb=len(bad), survivors=len(survivors),
        heldout_groups={s: len(got[s]) for s in got},
        roles=dict(collections.Counter(r[3] for r in rows)),
        new_split_files=dict(collections.Counter(r[2] for r in rows)),
        target_class_annotations={s: {c: per[s][c] for c in sorted(TARGET)} for s in ("train", "valid", "test")},
        verification_sift=dict(pairs=len(vp), threshold=SIFT_MIN,
                               heldout_train_pairs_at_or_above_threshold=sum(1 for s, *_ in scores if s >= SIFT_MIN),
                               max_score=scores[0][0] if scores else 0,
                               shared_filename_families=len(fam_leak),
                               note="inspect verify_top.csv in the viewer before trusting"),
        method_limits=["detectors are ORB/SIFT+RANSAC and can miss heavy crops or colour changes",
                       "only one representative image per group is compared",
                       "a passing check means 'no match found', not proof of no overlap"],
    )
    (OUT / "summary.json").write_text(json.dumps(summ, indent=2))
    print(json.dumps(summ, indent=2))
    print("done")

if __name__ == "__main__":
    sys.exit(main())
