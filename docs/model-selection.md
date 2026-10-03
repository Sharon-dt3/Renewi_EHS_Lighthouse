# Model selection and provenance

Inspection date: 2026-10-03. Decision: **no model approved**.

Paths such as `utils/`, `models/`, `temp-attachments/` and `kavia-docs/` named below refer to the outer workspace, not to this repository.

## Current direction: fine-tune Hafizqaim for five explicit target classes

Fine-tuning Hafizqaim is a proposed path to add an explicit **No-Safety Vest**
class, rather than treating "no vest detected" as negative-vest evidence. It is
not an owner decision and does not replace the earlier alternative-candidate
preparation. It grants no checkpoint-loading or rights approval.

### Original checkpoint preservation

The workspace `models/best.pt` is the immutable source artifact. Fresh
byte-only checks found **6,249,635 bytes** and SHA-256
`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`,
matching the user's required fingerprint. No checkpoint was loaded or written
during this assessment. Do not rename, replace, or save training results over
this file. Any authorized training run must mount the source read-only,
write to a distinct run directory, and verify the original digest before and
after execution. Record the new artifact's own hash; do not bind it to the
original class map or silently adopt it.

### Target taxonomy and available training inputs

The existing descriptor at `data/input/ppe5/data.yaml` uses this fixed order:

| Target display name | Training ID | Internal label |
| --- | --- | --- |
| Person | 0 | `person` |
| Helmet | 1 | `helmet` |
| No-Helmet | 2 | `no_helmet` |
| Safety Vest | 3 | `safety_vest` |
| No-Safety Vest | 4 | `no_safety_vest` |

These are **prospective training IDs**, not the original Hafizqaim IDs.
Its verified serialized taxonomy has `person`, `head_helmet`, `head_nohelmet`,
and `vest`, but no explicit negative-vest label. Runtime taxonomy and model
head behavior remain unverified. Adding an alias or editing a names map
cannot create a learned fifth target class.

Fresh workspace path discovery found the descriptor and empty
`images/train`, `images/val`, `labels/train`, and `labels/val` directories.
There are **zero training/validation image-label pairs** in that scaffold.
The scan excluded virtual environments, Git metadata, skills and node_modules;
AppleDouble `._*` sidecars are not samples. No training or authorization
manifest was identified by the bounded workspace discovery. This does not
prove that an external dataset or approval record cannot exist.

The workspace and application class-map configurations no longer advertise a
derived negative-vest class. Both analyzer implementations now return explicit
model detections only, and the legacy `NoVestDeriver` helper has since been removed from this repository.
Missing, low-confidence, occluded or out-of-frame vest detections leave vest
status **unknown**, not No-Safety Vest. Zone-person detection is unaffected.

### Required decisions before any training

1. **Renewi data/annotation owner:** supply accessible images with intended-use
   authorization and provenance, plus complete YOLO bounding-box annotations
   for all five target classes. Explicit negative-vest labels require a visibly
   assessable torso without a safety vest; occlusion or a detector miss is not
   a label. Agree consistent box conventions for persons, head PPE and vest
   states. Include diverse lighting, viewpoints, occlusion and vest styles;
   do not generate labels by subtracting vest detections from person detections.
2. **Dataset/evaluation owner:** document class counts, image-label integrity,
   class IDs and normalized box validity; split by source clip/site/session
   before extracting frames to prevent near-duplicate leakage. Supply a
   separately held-out authorized evaluation set. Previously requested
   5–10 representative inputs are smoke-test inputs, not evidence of adequate
   five-class training coverage.
3. **Rights/model owner:** accept digest-bound exact-weight rights for
   fine-tuning and intended use, dataset rights and relevant upstream/software
   obligations. `config/model.yaml` approval, actual-class verification and
   required-class support flags remain false; reviewer/license fields remain
   null. This instruction does not establish acceptance of those rights.
4. **Security/runtime owner:** authorize a digest-bound restricted loading and
   training harness for the Hafizqaim artifact and pinned packages. The existing
   preparation-only utility targets Baskarmother and denies all writes; it is
   neither a Hafizqaim training harness nor training authorization. A virtual
   environment alone is not hostile-checkpoint containment. Preserve CPU
   restricted-loading controls and stop on unapproved globals; do not use
   `weights_only=False`, an unrestricted YOLO object loader, or a blanket
   safe-global allowlist to bypass the unresolved gate. Review an explicit
   output-only write boundary for any future training environment.
5. **Training/model owner, after these gates:** adapt the detection head to the
   five target classes using a reviewed supported transfer path, train all five
   together to retain existing capabilities, and save a separate versioned
   checkpoint. Record seed, package/harness versions, dataset and source hashes,
   configuration, run logs, output hashes and per-class held-out precision,
   recall and mAP. Agree acceptance thresholds before evaluation, inspect
   runtime names/head and failure cases, and register only the validated new
   checkpoint's class mapping. Training alone does not approve deployment.

**Status: prerequisite assessment completed; training blocked. Checkpoint
loads: 0; training runs: 0; inference calls: 0; training metrics: not produced.**
The missing class has not yet been learned or validated. Earlier alternative
model evidence below is retained as history, not a model replacement decision.

### Verification of this change

Note: `NoVestDeriver` and `test_vest_rule.py` were removed in a later commit. The test counts below describe the earlier run.

Focused `test_vest_rule.py`, `test_pipeline.py`, `test_frame_pipeline.py` and
`test_class_map.py` runs passed **25 tests in the workspace layout** and
**25 tests in the application layout**, using the existing project virtual
environment with bytecode and pytest cache writes disabled. These are
synthetic rule/pipeline/configuration tests, not training or real-model
validation. They cover no negative-vest inference from absence, preservation
of explicit synthetic negative-class outputs, refusal to invoke a legacy
deriver, unchanged person-zone behavior and class-map handling.

Post-edit byte-only checks reconfirmed the original checkpoint at
**6,249,635 bytes**, SHA-256
`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`.
No dependencies were installed and no model approval flags were changed.

## Virtual-environment alternative preparation (not approved) — 2026-10-03

A prior session reports preparing an isolated alternative using the existing
project virtual environment. No approval for it is recorded in this
repository. Preparation is reported complete and its preflight passed; **checkpoint loading and real-model validation are not ready**.
This approval does not establish exact-weight rights, candidate selection,
sample authorization, or transfer the earlier container-specific loading
exception to host execution.

The preparation-only preflight utility
has no download, checkpoint-loading, safe-global addition, or inference mode.
Run it from the workspace root with:

```sh
Renewi_EHS_Lighthouse/.venv/bin/python -I -B utils/prepare_model_validation.py
```

### Verified execution evidence

- macOS 14.6 supplied `/usr/bin/sandbox-exec`; its activation probe succeeded.
  Docker, Podman, Colima and nerdctl were not found on PATH.
- The final sandboxed preflight exited **0**, with `preflight_passed: true`.
  It used Python **3.11.14** and existing virtual-environment packages:
  PyTorch **2.6.0**, Ultralytics **8.3.70**, OpenCV distribution **4.11.0.86**.
  Torch and OpenCV runtime imports succeeded. Ultralytics was checked through
  distribution metadata, not by invoking its object-checkpoint loader.
- The OS returned `EPERM` for exclusive file creation in the workspace,
  home directory and `/private/tmp`, outbound loopback socket connection,
  listening socket binding, and a `/usr/bin/true` child-process attempt.
  These are tested examples of policy enforcement, not a sandbox certification.
- The child receives an explicit minimal environment, excluding a synthetic
  parent sentinel and `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD`. Python uses `-I -B`,
  and `TORCH_FORCE_WEIGHTS_ONLY_LOAD=1` is set defensively; no `torch.load`
  call was made.
- Limits configured in the worker are 30 CPU seconds, zero core-dump bytes and
  128 open files; the parent enforces a 60-second wall timeout.
- The final harness SHA-256 was
  `0a1eb9db5493f8db0ea505f0dfe4e38c5857ead89e49bc6e581ff9c215d8d012`;
  generated sandbox-policy SHA-256 was
  `0974515d7953e9adff5dc3c612c9b4a47ec9a4d57922fa804825adb060204a93`.
  The utility emits current hashes and the actual policy on each run. These
  identify the tested preparation artifacts, not a security-owner review or
  digest-bound approval of a model-loading harness.
- Byte-only hashing reconfirmed local `models/best.pt` as 6,249,635 bytes,
  SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`
  (Hafizqaim). It does not match the Baskarmother target of 6,258,474 bytes,
  SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`.

### Isolation boundaries and readiness

The virtual environment isolates Python dependencies, **not hostile code**.
OS restrictions come from the sandbox policy, which allows operations by
default and explicitly denies filesystem writes, network operations, process
forks and executable launches except the Python executable needed for startup.
Because macOS's interpreter wrapper attempted another startup process, the
final utility invokes the same installed framework binary directly and
explicitly adds the existing virtual-environment site-packages.

Host file reads remain allowed under the current user's permissions.
Mach service lookup is not restricted; memory limits, separate user identity,
container/VM isolation, and a filesystem confidentiality boundary are absent.
No claim of comprehensive IPC denial, hostile-checkpoint containment, or
production readiness is made. The default-allow policy needs security-owner
assessment before any exceptional checkpoint reconstruction.

No dependencies were installed, no weights were downloaded or replaced, and
application configuration was unchanged: all three approval/verification flags
remain false, with reviewer and license fields null. **Checkpoint loads: 0;
prediction calls: 0; Renewi inputs processed: 0.** Runtime taxonomy, head
verification and detection capability remain unverified.

Before a loading trial, the security owner must review the tested alternative
and a digest-bound restricted loading harness. Keep `weights_only=True`, CPU
mapping, and the earlier symbol restriction: preparation does not authorize
`weights_only=False`, Ultralytics' unrestricted loader, or adding more globals.
The prior `DetectionModel` exception remains container-specific until a
separate decision explicitly covers this alternative. An unapproved global
must be reported and loading stopped, not automatically allowlisted.

The model/rights owners must separately record a Baskarmother digest-bound
selection and exact-weight intended-use rights, then authorize staging the
matching artifact. The Renewi evaluation owner must supply the authorized
5–10 representative inputs and manifest already requested below.
**OPEN-01 remains unresolved; this preparation does not unblock STEP-02 or FR-1.**

## Current model-validation gate recheck — 2026-10-03

The authoritative user-input attachment supplies the approved revision-1 core
PPE plan: STEP-02 remains blocked until OPEN-01 is resolved, and FR-2 remains
blocked until STEP-03 records successful real-model FR-1 verification. Its
initial repository inventory is historical context, not the current inventory:
the inspected application HEAD is `e42b392` (`Add PPE pipeline scaffolding
(unverified, no model loaded)`). Existing scaffolding does not satisfy model
approval.

### Results verified in this invocation

| Check | Result | Evidence boundary |
| --- | --- | --- |
| Pinned Baskarmother artifact | In-memory acquisition matched revision `3213ed51de90cbc76e577e6944e84f7c74343526`, size **6,258,474 bytes**, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. | Existing `utils/inspect_ppe_candidates.py --self-test baskarmother` inspected inert ZIP/pickle opcodes; no checkpoint copy was saved and no object was reconstructed. |
| Required serialized labels | ID 9 `person`, ID 4 `hardhat`, ID 6 `no-hardhat`, ID 12 `safety vest`, ID 8 `no-safety vest` all occur in the complete 17-entry literal map. | Metadata member is 104,137 bytes with 38,859 opcodes; two literal `nc: 17` fields agree, while one nonliteral `nc` reference remains uninterpreted. This is not runtime `model.names`, head verification or detection capability. |
| Current workspace `models/best.pt` | **6,249,635 bytes**, SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`: the recorded Hafizqaim fingerprint, not Baskarmother. | `utils/verify_local_ppe_checkpoint.py` exited 1 with `Fingerprint mismatch; no inspection or loading`, before Torch import/loading. This expected refusal is not a failed inference run or a successful Baskarmother validation. |
| Parser self-checks | **7 passed** in each invoked utility. | Inert, hand-authored parser cases only. |
| Downloader regression checks | **25 passed in 1.12s** using the nested application virtual environment and `backend/tests/test_download_model.py`. | Synthetic downloader/approval tests, including refusal before network access; not real-model validation. |
| Runtime availability | Host `python3.11` reports **3.11.14**. Neither `docker` nor `podman` was found on PATH. | No accessible approved container identifier or reviewed run package was established. Missing executables on PATH do not prove that no remote/container environment exists. A matching interpreter is not containment approval. |
| Validation inputs | Bounded workspace path discovery found no JPG/JPEG/PNG, MP4/MOV/AVI/MKV/WEBM, ZIP, or filename containing `manifest` or `approval`, excluding `.git`, `.venv`, `skills`, `node_modules`, and `__pycache__`. | This is candidate-path discovery, not exhaustive proof that no external media or differently named approval record exists. No authorized Renewi sample manifest was supplied. |
| Approval controls | `approved`, `actual_classes_verified`, and `required_classes_supported` remain false; configured reviewer/license fields remain null. | Configuration still names Hafizqaim; Baskarmother has not been adopted. |

These results were collected from tool stdout; no new raw execution log was
saved. Runtime `model.names` remains unobtained. **Renewi inputs processed: 0;
prediction calls: 0; detection/confidence records: none.**

### Concrete prerequisites and accountable actions

1. **Security owner and environment operator:** identify and provide access to
   the approved container, or separately authorize and demonstrate an isolated
   alternative with a digest-bound reviewed loading harness, dependencies and
   controls. The recorded conditional exception covers only `DetectionModel`
   with Python 3.11.14, PyTorch 2.6.0 and Ultralytics 8.3.70 in an approved
   container; it does not approve host execution or other serialized symbols.
   If an authorized restricted run requires another unapproved global, record
   the diagnostic and stop for a separate security decision.
2. **PoC/model owner and rights reviewer:** record a digest-bound candidate
   decision and accepted exact-weight intended-use rights, notices and relevant
   upstream/training-data obligations. The existing Baskarmother review records
   an MIT declaration, not accepted rights; this invocation did not refresh
   license sources. Prior asserted Hafizqaim permission must not be treated as
   Baskarmother permission or replacement approval.
3. **Renewi/evaluation owner:** provide accessible, authorized **5–10**
   representative images/clips and a manifest identifying inputs, positive and
   explicit-negative helmet/vest cases, and reviewed expected observations.
   Accuracy claims additionally require annotations and agreed acceptance
   criteria.
4. **Validation operator, after the above prerequisites:** stage and rehash the
   candidate-correct artifact inside the approved environment, obtain the full
   runtime taxonomy/head evidence, run the authorized smoke trial, and record
   input/frame identity, settings, class IDs/names, boxes and confidences.
   The separate annotated 100-clip evaluation is not replaced by this trial.

**Disposition: OPEN-01 unresolved; STEP-02 must not proceed.** No dependencies
were installed, no safe globals were added, no checkpoint was loaded, and no
application source or configuration was changed by this recheck.

## Correction: digest-bound taxonomy and pickle references

The statement that the recorded serialized map lacks an explicit negative-vest label applies only to Hafizqaim SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`. It does **not** apply to SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`, which the repository inspection utility identifies as Baskarmother. Both artifacts use the filename `best.pt` and contain 17 serialized labels, but their maps differ. Filename and class count are therefore insufficient identity evidence.

### Artifact reconciliation and origin of the disputed statement

This correction rechecked the current local checkpoint as inert bytes and independently rechecked the pinned Baskarmother source through a bounded, in-memory download. Neither checkpoint was unpickled or executed, and no downloaded checkpoint copy was written.

| Verified artifact | Size and SHA-256 | Relevant literal serialized labels | Negative-vest finding |
| --- | --- | --- | --- |
| Current local `models/best.pt`, matching the Hafizqaim `v1.0.0` fingerprint in `utils/inspect_hafizqaim_checkpoint.py` | 6,249,635 bytes; `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836` | ID 8 `face_nomask`; ID 12 `head_helmet`; ID 13 `head_nohelmet`; ID 14 `person`; ID 16 `vest` | No explicit negative-vest label in the complete 17-entry literal map |
| Baskarmother `best.pt`, revision `3213ed51de90cbc76e577e6944e84f7c74343526`, identified by `utils/inspect_ppe_candidates.py` | 6,258,474 bytes; `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe` | ID 4 `hardhat`; ID 6 `no-hardhat`; ID 8 `no-safety vest`; ID 9 `person`; ID 12 `safety vest` | Explicit negative-vest label present; `required_serialized_labels_match: true` reproduced using the verifier's required map and comparison |

The disputed paragraph is in “Requested loading and evaluation decisions — 2026-10-03”, under “Model owner: taxonomy examination cannot establish detection behavior”. That review explicitly identifies the Hafizqaim `5464…0836` artifact, and its statement is corroborated by the [complete observed serialized class list](#complete-observed-serialized-class-list), reproduced from the current local bytes. The [uploaded local checkpoint validation](#uploaded-local-checkpoint-validation--2026-10-03) and [complete observed serialized taxonomy](#complete-observed-serialized-taxonomy) concern the different Baskarmother `8714…1ffe` artifact. The ambiguity came from insufficient artifact qualification in the disputed sentence, not evidence that Baskarmother lacks the label. The original prose-generation history is not available, so no further causal claim about how the sentence was authored is established.

The comparison is case-sensitive, but it expects the exact lowercase serialized spelling, not `NO-Safety Vest`. In `utils/verify_local_ppe_checkpoint.py`, `main()` uses the following module-level values and expression:

```python
EXPECTED = CANDIDATES["baskarmother"]
REQUIRED = {
    9: "person", 4: "hardhat", 6: "no-hardhat",
    12: "safety vest", 8: "no-safety vest",
}

names = report["literal_names_maps"][0]["names"]
# Value assigned to required_serialized_labels_match:
all(names.get(key) == value for key, value in REQUIRED.items())
```

Thus the user's `required_serialized_labels_match: true` observation agrees with the Baskarmother fingerprint and exact labels. A comparison against uppercase `NO-Safety Vest` would fail literal equality, but that is not the comparison implemented here. The Hafizqaim inspector performs no required-target label comparison; its `main()` verifies its own size/hash and extracts literal `names` and `nc`. The local verifier rejects a fingerprint mismatch before metadata inspection or loading, so it must not be presented as a successful verifier run for the current Hafizqaim file. Only its static comparison expression was reproduced for Baskarmother during this correction; its loading path was not run.

### Eight Ultralytics references are verified, not eight approved exceptions

The current Hafizqaim `best/data.pkl` contains **eight distinct Ultralytics `GLOBAL` references**, not only `DetectionModel`. The following byte offsets were obtained by `pickletools.genops` without resolving or importing the referenced implementations. Independent static inspection of the pinned Baskarmother bytes found the same eight symbol names; the offsets below apply only to Hafizqaim.

| Serialized symbol, written as module plus attribute | Hafizqaim `GLOBAL` byte offset | Approval distinction |
| --- | --- | --- |
| `ultralytics.nn.tasks.DetectionModel` | 236 | Only class-specific exception recorded in the supplied task context, conditional on the specified dependencies and approved container |
| `ultralytics.nn.modules.conv.Conv` | 1039 | Referenced; no additional approval established |
| `ultralytics.nn.modules.block.C2f` | 4063 | Referenced; no additional approval established |
| `ultralytics.nn.modules.block.Bottleneck` | 7022 | Referenced; no additional approval established |
| `ultralytics.nn.modules.block.SPPF` | 36031 | Referenced; no additional approval established |
| `ultralytics.nn.modules.conv.Concat` | 39609 | Referenced; no additional approval established |
| `ultralytics.nn.modules.head.Detect` | 66345 | Referenced; no additional approval established |
| `ultralytics.nn.modules.block.DFL` | 86095 | Referenced; no additional approval established |

`utils/inspect_ppe_candidates.py`, `metadata_report()`, records literal `GLOBAL` arguments rather than a required exception manifest:

```python
globals_seen = set()
for index, (opcode, argument, offset) in enumerate(operations):
    if opcode.name == "GLOBAL":
        globals_seen.add(argument)
```

The local static pass also checked for `STACK_GLOBAL` and found none. Hafizqaim contains 23 distinct `GLOBAL` references in total: these eight Ultralytics references and 15 built-in, collections or Torch references. Baskarmother contains 24, including an additional `torch.nn.modules.linear.Identity` reference. These totals are different from a loader's list of globals not default-allowlisted. The historical Baskarmother report of 16 non-default-allowlisted globals is a separate, environment-dependent observation and must not be substituted for the current Hafizqaim reference list.

**Referenced symbols**, **globals required for a particular loading method**, and **approved exceptions** are separate evidence categories. The static list verifies names encoded in this pickle, not that every name needs an additional safe-global registration, that reconstruction would succeed, or that the implementations are safe. The reported restricted-loader diagnostic naming `DetectionModel` identifies the first reported refusal, not the complete required set. No digest-bound, implementation-reviewed minimal loading manifest has been established here, and no runtime requirement test was performed. Any future manifest must account for the full reference set, existing framework defaults, the exact loader and package artifacts, reconstruction behavior and limitations; it must not automatically convert the eight references, or all 23 references, into an allowlist.

This correction **does not expand approval**. The supplied prior exception remains limited to `DetectionModel` with Python 3.11.14, PyTorch 2.6.0 and Ultralytics 8.3.70 in an approved container; no accessible identified approved environment is established. If an authorized future restricted run needs any additional unapproved global, it must record the diagnostic and stop pending a separate explicit security decision. No safe globals were registered, no checkpoint was loaded, and no inference, source-code edit or configuration change occurred. The [configured approval flags](../config/model.yaml) remain false.

### Focused verification and limits

The current Hafizqaim archive yielded 363 members, one `best/data.pkl` of 95,730 bytes, 37,805 inert opcodes, one complete literal names map spanning offsets 88479–88862, and two literal `nc: 17` fields. The Baskarmother metadata member was 104,137 bytes with 38,859 inert opcodes and a complete 17-label map spanning offsets 88723–89098; its two literal `nc` fields also equal 17. Each report retains one uninterpreted nonliteral `nc` reference. All seven inert parser self-checks passed. The evidence was collected from tool stdout, not a saved verifier-log file. Torch and Ultralytics were not imported during these checks.

These observations verify artifact identity, literal serialized taxonomy and encoded global references only. They do not establish runtime `model.names`, output-head agreement, detection quality, safe reconstruction, rights acceptance or model adoption. Baskarmother's explicit negative-vest label is present in the serialized map; Hafizqaim's absence remains a digest-specific static finding, not a case-normalization failure.

## Mac-based restricted loading: security-review disposition

**Direct execution on the Mac is not within the recorded approval scope, and this assessment grants no approval.** The current request reports permission to use the verified Hafizqaim checkpoint for the Renewi PoC. The supplied task context records prior authorization for only `ultralytics.nn.tasks.DetectionModel`, using Python **3.11.14**, PyTorch **2.6.0** and Ultralytics **8.3.70**, specifically in an **approved container**. No approved container identifier is available, and no separate Mac-based security authorization or demonstrated containment is established. That conditional authorization does not transfer to the host Mac, a virtual environment, an arbitrary container or an unreviewed VM.

The user's permission assertion is recorded as current supplied information, not an independently validated rights determination. Earlier rights and exception dispositions below describe their earlier evidence state; they must not be read as disproving the current assertion or as granting broader execution rights. Rights permission, a class-specific loading exception, environment approval and model adoption are separate decisions. The missing approved execution environment remains the operational blocker even accepting the supplied checkpoint identity and permission.

The assessment concerns only `models/best.pt`, reported as **6,249,635 bytes** with SHA-256 **`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`**. These bytes were not reverified or loaded during this review. The allowed purpose remains restricted loading and taxonomy inspection only, with no inference, training, conversion, application integration or adoption.

### Why the proposed host procedure is insufficient

Python version matching and `weights_only=True` do not establish a containment boundary. Restricted loading reduces pickle reconstruction exposure but is not a sandbox or a guarantee against resource exhaustion, unsafe behavior in allowed implementations, dependency/native-code vulnerabilities or unsafe handling of reconstructed objects. Allowlisting a class authorizes reconstruction of that implementation; its name and the checkpoint digest do not certify it as safe. A scoped safe-global context limits registration lifetime, not filesystem or network access. A virtual environment isolates dependencies, not the host user's files, credentials, network access or privileges.

A disposable, security-reviewed VM hosted on a suitable Mac is a candidate for separate review, not permission to load directly on macOS. A container running through a Mac VM still requires review of both boundaries and all host integrations; the product name or presence of virtualization is insufficient. Turning off Wi-Fi, relying on an application firewall or using a separate nonadministrator account alone does not demonstrate the required isolation.

### Containment requirements for reviewer consideration

The following are proposed acceptance requirements, not controls demonstrated on this Mac. The designated security owner must accept the actual implementation and residual risks before any loading attempt; meeting this table does not automatically extend the container-only authorization.

| Control area | Required implementation and review evidence |
| --- | --- |
| Explicit scope and identity | Record a dated, accountable authorization for the specific Mac-hosted environment or identify the existing approved container. Bind the decision to host/guest identifiers, OS and architecture, hypervisor or runtime version, guest-image digest, checkpoint digest, reviewed harness digest, dependency artifact hashes, permitted class, purpose, operator, expiry and re-review triggers. |
| Disposable boundary | Use a fresh disposable guest on a reviewer-accepted, patched nonproduction host. Document the isolation mechanism and its limitations. Disable shared folders, automatic host-volume mounts, clipboard sharing, drag-and-drop, USB/device passthrough and unnecessary guest integrations. Do not expose this workspace or the external volume to the guest. |
| Network denial | Provision reviewed dependencies before staging the checkpoint, then disconnect guest network adapters and enforce denial outside the guest for ingress and egress, including IPv4, IPv6, DNS, host-only and bridged access. Demonstrate denied access using benign probes before staging the checkpoint; retain external enforcement records. Guest settings alone are insufficient. |
| No secrets or privileged access | Use a fresh nonadministrator guest identity without sudo, host login material, Keychain access, SSH agents, cloud credentials, tokens, production data or authenticated host services. Expose no container-engine socket or privileged management interface to the guest. Keep execution CPU-only with no GPU/device passthrough. |
| Immutable minimal input | Stage only the approved checkpoint through a controlled transfer, not a host share. Present it read-only, reject symlinks and unexpected inputs, verify size and SHA-256 inside the guest and load the same verified bytes without reopening a mutable path. Permit writes only to bounded guest scratch/output storage. |
| Reviewed dependencies and harness | Verify Python 3.11.14, PyTorch 2.6.0 and Ultralytics 8.3.70 against reviewed artifacts and guest-platform compatibility. Use an offline, candidate-correct, independently reviewed harness in a fresh process. Retain explicit `weights_only=True` and CPU mapping; prohibit loader wrappers, remote downloads, environment overrides and fallback paths. Verify the expected framework registry and refuse unexplained pre-existing additions. |
| Enforced resource limits | Record reviewer-approved numerical limits for VM memory, CPU allocation, process count, disk/scratch capacity, output bytes and wall-clock time, plus the means of enforcement. Use an external watchdog that can terminate the entire guest. Demonstrate termination and limits with benign probes; thread limits or Python exception handling alone are not containment. |
| Minimal evidence export | Allow only size-bounded plain text or schema-validated JSON containing identity, versions, complete taxonomy and diagnostics. Treat guest output as untrusted, escape control characters and reject executable content, serialized objects, checkpoints and malformed output. Use a controlled export step rather than a continuously writable host share. Keep host-controlled audit timestamps and termination records. |
| Incident handling and teardown | Record who terminates the guest, preserves policy-approved evidence and assesses suspected escape or unexpected access. After evidence review, destroy the guest, snapshots, scratch disks and staged checkpoint copies under the retention policy. Do not resume or reuse a contaminated guest. |

The operator must retain benign-probe results demonstrating network denial, unavailable host resources, blocked input writes and enforced resource/output limits before a reviewer can assess readiness. This review ran no such probes and asserts no sandbox is available.

### Loading scope, stop conditions and unresolved evidence

If an authorized future run requires any global beyond the specifically authorized `ultralytics.nn.tasks.DetectionModel`, it must record the bounded diagnostic and stop. Do not incrementally add classes, clear or broaden the registry, retry with `weights_only=False`, bypass the restricted loader through `YOLO(...)`, or change package versions to obtain a successful load. This assessment registers no class and provides no loading command. Stop also on absent or expired authorization, identity/version mismatch, unexpected registry or loader behavior, attempted host/network access, exhausted limits or malformed evidence.

Repository source review shows that `utils/inspect_hafizqaim_checkpoint.py` downloads and examines inert metadata; it is not an offline runtime-loading harness. `utils/verify_local_ppe_checkpoint.py` targets Baskarmother and must not be reused as a Hafizqaim loading procedure. Neither establishes the requested containment. The configured model remains `approval.approved: false`, with runtime-class verification and required-class support unset.

The security owner and environment operator must supply an identified approved container or a separately authorized, evidenced Mac-hosted isolated environment and reviewed run package before work can resume. Even a future successful restricted load would establish only the reported taxonomy observation, not safe model behavior, complete PPE coverage or model acceptance. No checkpoint loading, safe-global registration, containment execution, inference, training, source-code changes or configuration changes occurred in this assessment.

## Requested loading and evaluation decisions — 2026-10-03

This disposition addresses the five decisions in the
authoritative request.
It concerns only workspace `models/best.pt`, reported as 6,249,635 bytes with
SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`.
Identity verification is accepted as prior recorded evidence, not reproduced
here. The conclusions below are technical recommendations, not authorized
owner approvals or a finding that the checkpoint is malicious.

### Security: no safe-global exception justified

Do not approve or register `DetectionModel` or any additional symbol on the
present evidence. The reported refusal identifies one unsupported global,
not the exact minimal required list or its safety. Missing evidence is a
digest-specific minimal manifest with each symbol's necessity, resolved
implementation, package hash and review of imports, reconstruction and
state-restoration behavior. Static enumeration alone is insufficient.
The designated security owner must first decide whether policy permits an
exception and then record a scoped decision on the complete reviewed package;
this review grants none.

### Loading harness: approval pending a candidate-correct reviewed package

Do not approve the harness or dependency set yet. Source review confirms
that `utils/verify_local_ppe_checkpoint.py` targets Baskarmother, while the
Hafizqaim inspector downloads its input and is not an offline runtime loader.
Python 3.11.14, PyTorch 2.6.0 and Ultralytics 8.3.70 are the recorded baseline,
not an approved execution environment. The backend lockfile pins package
versions but has no artifact hashes and describes macOS ARM64.
Missing evidence includes an independently reviewed Hafizqaim harness,
its digest and exact invocation, immutable-byte identity enforcement,
hashed dependencies, guest-platform compatibility and vulnerability review,
and fail-closed handling without unrestricted fallback or incremental
allowlisting. The designated security reviewer must approve or reject that
exact package and scope; existing acquisition gates must not be relaxed.

### Isolation: useful proposal, sufficiency not demonstrated

Do not confirm containment readiness from narrative controls alone.
The proposed disposable VM, externally enforced network denial, absent host
shares and credentials, nonprivileged CPU-only execution, read-only input,
resource limits and bounded output are appropriate review requirements.
A container alone is not established as an equivalent boundary.
Missing evidence includes the identified guest image and host/hypervisor
configuration, numerical limits, benign control-probe results, output
validation, incident handling and teardown records. The security owner and
operator must document the actual boundary and accept demonstrated controls
before any checkpoint test.

### Rights: Renewi PoC and runtime-evaluation permission unresolved

Do not confirm permission for these exact weights. The recorded primary-source
review found no affirmative exact-weight license grant and no maintainer
response to the existing inquiry. Public download instructions and a matching
mirror establish neither Renewi permission nor upstream/data clearance.
Missing evidence is a durable digest-bound grant from an authorized
rightsholder covering the actual entities and internal evaluation activities,
reconciled upstream/software/data obligations, and a dated acceptance by the
designated rights reviewer. This is an unresolved permission gate, not a
definitive legal prohibition; isolation and PoC status do not resolve it.

### Model owner: taxonomy examination cannot establish detection behavior

Do not confirm the proposed procedure as sufficient for model acceptance.
It is a taxonomy/head examination proposal with no prediction calls.
For Hafizqaim SHA-256
`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`,
the complete recorded 17-class literal map has ID 16 `vest` and no explicit
negative-vest label. This does not describe Baskarmother SHA-256
`8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`,
whose map contains ID 8 `no-safety vest` and ID 12 `safety vest`; see the
[digest-bound correction](#correction-digest-bound-taxonomy-and-pickle-references).
Runtime names, output-head agreement and detections remain unverified.
A successful load would not prove semantics or five-class coverage.
Missing evidence includes reconciled digest-bound runtime taxonomy/head and
annotation semantics, plus separate evaluation on authorized annotated
fixtures with owner-agreed metrics and acceptance criteria, real Person/PPE
outputs and application mapping/association checks. Absence of `vest` must
not be relabeled as `no_safety_vest`. The model owner must separately decide
whether limited examination is worth pursuing and how to address the coverage
gap; that authorization would not constitute adoption or an FR-1 pass.

### Review boundary and unchanged status

DocumentManager returned no registered sources or change history, so the
existing findings and supporting configuration, utility, downloader and
dependency files were inspected directly. Historical rights findings and
runtime observations were not independently refreshed or reproduced.
Only this existing document is amended. No checkpoint was read or loaded,
no model packages imported, no safe globals changed, no sandbox provisioned
and no inference, training or dependency installation performed.
`approved`, `actual_classes_verified` and `required_classes_supported` remain
false. All five owner decisions are outstanding; runtime loading, inference
and model approval remain paused.

## Loading-proposal review: explicit allowlisting is not justified

**Review disposition: insufficient evidence for any class-specific loading
exception; no organizational security approval or execution authorization is
granted.** This review concerns only Hafizqaim `best.pt`, 6,249,635 bytes,
SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`.
The reported fingerprint and restricted-load refusal are prior evidence, not
observations reproduced during this review. Runtime validation, inference,
training, conversion, integration and model approval remain paused. No class
has been added to a safe-global registry.

### Assessment of the existing containment proposal

The proposal below provides a useful review baseline: immutable verified
input, a disposable VM rather than a virtual environment alone, externally
enforced network denial, no host shares or credentials, nonprivileged CPU-only
execution, resource limits, bounded untrusted outputs and documented teardown.
It correctly separates security, rights, examination authorization and model
adoption. These are proposed controls, not demonstrated containment.
There is no completed run package, independently reviewed loader, identified
VM image or recorded containment-probe evidence establishing readiness.

The existing proposal deliberately prohibits safe-global expansion and stops
on restricted-load refusal. Explicit allowlisting would therefore be a
different reconstruction proposal, not an implementation detail already
covered by this procedure. A disposable VM reduces exposure but does not
make otherwise prohibited loading permissible or certify the artifact.

### Why the digest and class error are insufficient

The unsupported `ultralytics.nn.tasks.DetectionModel` diagnostic identifies
the first reported restriction, not a complete list of required classes or
evidence that their implementations are safe. No complete, reviewed
Hafizqaim-specific exception manifest is established. Historical scan results
for Baskarmother must not be reused for these different bytes. This review
does not designate `DetectionModel`, other Ultralytics classes, or additional
PyTorch classes as safe.

The [PyTorch 2.6 serialization guidance](https://docs.pytorch.org/docs/2.6/notes/serialization.html)
states that allowlisted functions can be called and classes instantiated with
state set during unpickling. It also warns that static global enumeration can
miss dynamically constructed types. Thus, an unsupported-global message or
static scan is an inventory input, not a trust decision. Importing a named
class also executes dependency import code; familiar package or class names
do not establish the provenance of the resolved implementation.

PyTorch safe-global registration does not itself bind permission to a file
digest. Any future digest-bound exception would need enforcement by a
separately reviewed harness using exactly the verified immutable bytes,
with no other checkpoint loaded while an exception is active. A scoped
context would limit registration lifetime, not provide a sandbox or a
cryptographic authorization boundary. Residual risks include unsafe
reconstruction/state-restoration behavior, hostile downstream objects,
dependency/native-code vulnerabilities, resource exhaustion, fabricated
taxonomy evidence, and containment or evidence-export failures.

### Evidence required before a reviewer can consider an exception

If organizational policy permits considering an exception at all, the
security owner must require a fixed, minimal manifest for this exact digest.
For each proposed symbol, the submission must identify its serialized name,
resolved runtime object, package artifact/hash and implementation location;
explain why reconstruction requires it; and record source-review findings
for imports, inherited reconstruction/state-restoration behavior and reachable
helpers. Review must cover the loader and any taxonomy/head inspection code,
not just a class constructor. Unknown symbols, aliases, module shadowing,
custom code or unexplained state must remain grounds to refuse the proposal.

The run package must bind that manifest to the harness digest, exact
invocation, reviewed dependency artifacts, guest image, platform, numerical
resource/output limits, control-probe evidence and decision expiry. The
repository's requirements pin versions, including Torch 2.6.0 and Ultralytics
8.3.70, but `requirements.lock` contains no package hashes and describes a
macOS ARM64 resolution, not an approved VM environment. Vulnerability,
provenance and guest-platform compatibility assessments remain required;
this review has not audited those installed package implementations.

Any future harness proposal must retain explicit restricted loading and CPU
mapping, verify the reviewed registry baseline before and after any scoped
exception, prohibit concurrent/unrelated loads, and terminate its fresh
process after the bounded examination. It must not import symbols chosen by
checkpoint strings, bulk-register scan results, clear unexpected registrations,
retry with newly discovered classes, or fall back to unrestricted pickle,
loading overrides or a bypassing wrapper. A new unsupported symbol means
stop and renewed review, not incremental expansion until loading succeeds.
These are review requirements only; no executable exception is supplied.

### Required owner decisions and unchanged gates

| Decision | Required record and accountable owner | Current disposition |
| --- | --- | --- |
| Whether any exception is permissible | The designated security owner must decide whether policy permits class-specific reconstruction and why its bounded information value warrants the residual risk. | Not established; no exception justified by present evidence. |
| Exact reconstruction scope | The security reviewer must accept or reject every symbol and the complete versioned harness/environment package, record identity, date, constraints and expiry, and define re-review triggers. | No approved manifest or executable harness. |
| Operational containment | The security owner and operator must identify the VM/host boundary, demonstrate controls with benign probes, and agree termination, incident handling, evidence retention and teardown. | Narrative controls only; readiness not demonstrated. |
| Rights for the bounded examination | The designated rights reviewer must record permission and applicable obligations for these exact weights and dependencies. | Exact-weight rights remain unresolved. |
| Whether taxonomy examination is worth pursuing | The model owner must explicitly authorize only the limited examination and address the recorded missing negative-vest class without asserting five-class acceptance. | Runtime taxonomy/head evidence remains unverified. |
| Later model/application acceptance | The model/application owner must separately accept rights, capability and required evaluation evidence before adoption or an FR-1 pass. | No model approved; FR-2 is not unblocked. |

The reported initial identity validation must not be described as a completed
application FR-1 pass. The recorded serialized taxonomy lacks an explicit
`No-Safety Vest` output; a successful load would not resolve that gap, prove
detections or grant rights. Absence of a `vest` detection must not be relabeled
as `no_safety_vest`.

### Review evidence and validation limits

Source review confirms that `utils/verify_local_ppe_checkpoint.py` targets
Baskarmother and cannot serve unchanged as a Hafizqaim harness. The Hafizqaim
inspector parses inert metadata but its entrypoint downloads weights; it is
not this procedure's offline runtime loader. The guarded downloader checks
approval before acquisition and does not deserialize weights.
`config/model.yaml` still sets `approved`, `actual_classes_verified` and
`required_classes_supported` to false.

DocumentManager returned no registered document sources or change history,
so the existing proposal and supporting sources were read directly. Review
was limited to documentation, configuration, repository utility source and
official serialization guidance. No checkpoint was read or loaded, no model
packages were imported, no sandbox was provisioned, and no dependency audit,
control probes or runtime tests were executed. Only this existing document
is amended; configuration, source code, weights and approval status are
unchanged. Further runtime work requires the separate recorded owner
decisions above, not approval inferred from this review.

## Proposed Hafizqaim isolated-loading procedure and security review — 2026-10-03

**Status: proposal only; security approval, rights clearance and execution
authorization are not established.** The
authoritative request
asks for an approved, security-reviewed procedure. This document supplies a
reviewable proposal, not that approval. It authorizes no checkpoint loading,
inference, training, conversion, integration or model adoption. No such
operation was executed for this documentation update.

### Exact scope and evidence baseline

The sole input is Hafizqaim `v1.0.0`, release asset `273300310`, `best.pt`,
**6,249,635 bytes**, SHA-256
**`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`**.
The attachment reports that these bytes were verified and that Python
**3.11.14**, PyTorch **2.6.0** and Ultralytics **8.3.70** were used. It reports
restricted `torch.load(..., weights_only=True)` refusal at
`ultralytics.nn.tasks.DetectionModel`, with no unsafe workaround or safe-global
expansion. These are supplied observations, not a load reproduced here.
The latest local-identity record identifies
`models/best.pt` as Hafizqaim; earlier Baskarmother
observations concern different bytes at that path and remain historical.

The [recorded complete serialized taxonomy](#complete-observed-serialized-class-list)
contains 17 labels, including ID 12 `head_helmet`, ID 13 `head_nohelmet`,
ID 14 `person` and ID 16 `vest`, but no explicit `No-Safety Vest` equivalent.
This is inert metadata evidence, not runtime `model.names`, verified head
structure or demonstrated detections. Hash agreement is identity evidence,
not a safety certificate or rights grant. The loader refusal is not proof of
maliciousness or universal incompatibility.

### Required review and written authorization before execution

The security reviewer must examine a complete, versioned run package before
authorizing a trial. It must bind the checkpoint digest to the loader script's
digest, exact invocation, dependency artifacts and hashes, environment image
identity, operating system/architecture, isolation configuration, resource
limits, permitted output schema, stop conditions and teardown procedure.
Reviewer identity, decision, date, permitted operations, constraints and expiry
must be recorded. No approved script, image, sandbox or decision record is
currently established; placeholders or this narrative must not become an
executable run authorization.

The review must trace actual dependency loading behavior, including wrappers
that might silently select unrestricted pickle, alter safe globals, retrieve
weights or import checkpoint-specified code. Static global scans and package
version strings are inputs to review, not complete safety assessments.
The observed stack is a reproducibility baseline, not an endorsement of its
current security posture. Review dependency vulnerabilities and provenance;
any necessary version change requires a new pinned package and compatibility
review rather than an in-session upgrade.

The designated rights reviewer must separately record whether the intended
bounded security/runtime examination is permitted for these exact weights
and applicable software. The [exact-weight rights review](#hafizqaim-exact-weight-licensing-and-provenance-review--2026-10-03)
remains unresolved; public availability or an isolated PoC is not permission.
The model owner must separately authorize the limited taxonomy examination.
That authorization must not depend on pretending five-class acceptance has
already passed. Security authorization, rights acceptance, experimental
execution authorization and adoption are distinct decisions.

### Proposed isolation and containment

Treat the checkpoint and anything it could cause to execute as untrusted.
Prefer a disposable VM on a security-controlled, nonproduction host with an
approved hypervisor boundary. A virtual environment alone is not a sandbox,
and a container alone must not be assumed to provide the required boundary.
On the recorded macOS host, selection and provisioning of an actual VM
remain security-owner responsibilities; no available sandbox is asserted.

Provision reviewed dependencies before introducing the checkpoint, then
disable guest network interfaces and deny host-side ingress/egress. Use a
nonadministrator guest account, CPU only, no device passthrough, no privileged
mode, no host runtime sockets, and no shared clipboard, host folders, home
directories, SSH agents, credentials or production services. Do not mount
the application repository or supply worker footage for taxonomy inspection.
Deliver only the exact checkpoint through a reviewed read-only input medium.
Separate reviewed code/dependencies from that input and permit writes only
to disposable scratch storage with reviewer-set CPU, RAM, disk, process and
wall-clock limits.

Before introducing the untrusted input, the operator must demonstrate the
isolation controls using benign probes: denied network access, unavailable
host resources, nonprivileged identity, read-only inputs and effective resource
limits. Retain the host-controlled configuration and probe results. Denial
must be enforced outside the potentially compromised guest, not merely by a
Python setting. Missing or failed controls prohibit loading.

### Gated examination sequence

First, after all preceding authorizations, the operator must verify inside
the guest that the input is a regular nonsymlink file of the specified size
and digest. Use the same immutable, read-only verified bytes for any later
attempt; do not reopen a mutable path that could change after hashing.
Stop on any identity, packaging, environment or permission mismatch. Record
environment versions and the actual invocation without publishing secrets.

Second, perform only reviewer-approved bounded inert archive/opcode inspection
and preflight checks. Do not extract arbitrary archive paths or interpret
pickle object/call opcodes. The
Hafizqaim inspector is evidence
of an inert parsing approach, but its main entrypoint fetches the release
over the network; it is not an offline local loader and must not be run as
this procedure's executable harness.

The existing local verifier
sets `EXPECTED = CANDIDATES["baskarmother"]` and checks Baskarmother's five
IDs/names. It therefore cannot validate Hafizqaim unchanged: it should reject
the current Hafizqaim fingerprint before loading. Even its successful
restricted-load branch does not instantiate a detector or retrieve runtime
names. A candidate-correct, independently reviewed examination harness is
still required; neither relaxing its fingerprint checks nor swapping class
expectations during execution is acceptable.

Third, a specifically authorized restricted attempt may use explicit
`weights_only=True` and CPU mapping in a fresh process. The harness must
reject loading overrides and unexpected safe-global registrations, must not
clear or expand the registry, and must have no automatic fallback. Static
scan output does not justify adding each listed global to an allow-list.
Given the reported refusal, this proposal offers no reason to expect that
the unchanged restricted attempt can reconstruct the detector.

If the restricted attempt refuses `DetectionModel` or another object, record
the diagnostic and stop. **This proposal does not approve `weights_only=False`,
safe-global expansion, security-environment overrides, a `YOLO(...)` wrapper
that bypasses restricted loading, remote code, or automatic conversion.**
Isolation reduces exposure; it does not authorize a prohibited operation.
If security policy permits considering a different reconstruction method,
the security owner must review that concrete method and its code/dependencies
as a new proposal and issue explicit, digest-bound authorization before any
attempt. If policy does not permit it, runtime verification remains blocked;
request trustworthy publisher evidence or separately consider an eligible
replacement rather than bypassing the restriction.

### Runtime taxonomy evidence and the negative-vest decision

Only if a permitted, separately reviewed method actually reconstructs the
detector may the operator record its complete runtime `model.names`, preserving
every raw ID/name without filtering or aliases. Identify the selected checkpoint
component, such as model versus EMA, and any wrapper transformations. Check
contiguous unique IDs, class-count and output-head agreement through the
reviewed method, and compare the complete runtime map with the recorded
17-entry serialized map. A discrepancy stops acceptance and requires
investigation; it must not be hidden by renaming or selecting a favorable map.
Runtime-exposed names alone still do not prove annotation semantics or correct
detections, especially if arbitrary checkpoint code could fabricate output.

| Requested canonical target | Recorded serialized ID/name | Runtime status for this request |
| --- | --- | --- |
| `person` | 14 / `person` | Unverified |
| `helmet` | 12 / `head_helmet` | Unverified; normalization remains conditional |
| `no_helmet` | 13 / `head_nohelmet` | Unverified; normalization remains conditional |
| `safety_vest` | 16 / `vest` | Unverified; normalization remains conditional |
| `no_safety_vest` | No explicit equivalent in the complete recorded map | Unsupported by recorded taxonomy; runtime/head evidence not obtained |

If runtime/head evidence agrees with the recorded taxonomy, document that
this checkpoint lacks the required explicit negative-vest output class and
does not satisfy the unchanged five-class contract. A claimed contrary
runtime label requires reconciled digest-bound head/semantics evidence, not
an invented alias. Never infer `no_safety_vest` from an absent `vest`
detection; insufficient or contradictory evidence remains UNKNOWN.
Training a missing class would produce new weights with new rights, identity,
security and capability gates, and is not authorized here.

A complete taxonomy/head check is only one prerequisite to FR-1 validation.
It cannot pass the full application gate or unblock FR-2. Real Person/PPE
outputs on authorized annotated fixtures, application mapping/association
and compliance checks, the required evaluation and explicit acceptance
remain separate work. No prediction or training call belongs to this
taxonomy-only procedure.

### Evidence release, stop conditions and teardown

Use host-controlled audit records for environment identity, containment
configuration, operator/reviewer decisions, input fingerprint, start/end
times, invocation, termination status and resource-limit events. The permitted
guest output should be bounded plain text or strictly validated JSON containing
versions, complete raw taxonomy, reviewed head checks and diagnostics only.
Treat all guest output as untrusted: validate its size/schema and review it
outside the VM without executing it. Do not export pickle objects, executable
files, converted weights or arbitrary guest archives into the application.

Stop on missing authorization, digest or version mismatch, unexpected loader
behavior, restricted-load refusal, attempted network/host access, resource
exhaustion, malformed output or taxonomy/head disagreement. Terminate the
trial, preserve only policy-approved evidence and have the security owner
assess any suspected containment failure before retrying. Destroy the VM,
scratch disk and staged copies after evidence review under the retention
policy; document teardown. A successful run is an observation, not approval
for later use.

### Present outcome and documentation validation

This proposal was checked against the authoritative attachment and current
configuration, dependency pins, acquisition gate and inert inspector/verifier
source. DocumentManager returned no tracked source history for this existing
document, so source files were read directly. No new checkpoint identity or
runtime result is claimed; the attachment and earlier records are explicitly
attributed. Source review confirms that the guarded downloader requires
complete approval before acquisition and never deserializes weights.

Only this existing evidence document is updated; no new published page,
Spec Builder artifact or implementation plan is created. No executable harness
is delivered or run, no dependencies are installed, and no checkpoint loading,
inference, training, conversion or evaluation occurs. The checkpoint, source
code, configuration and plan status remain untouched. `approved`,
`actual_classes_verified` and `required_classes_supported` remain false.
The security owner must supply the reviewed run package and decision; the
rights reviewer and model owner must supply the separate scoped clearances.
**No approved loading procedure is established, runtime taxonomy remains
unverified, and implementation/inference remain paused.**

## Hafizqaim exact-weight licensing and provenance review — 2026-10-03

**Outcome: rights unresolved for use, fine-tuning and deployment; no model
approved.** Primary-source refresh began at **2026-10-03 12:33:15 UTC**;
supplemental pinned-text checks began at 12:33:28 UTC, with compact evidence
retrieval at 12:33:53 UTC after tool-output truncation. This is an evidence
review, not legal advice, a definitive prohibition finding or authorization
to train, load or run the checkpoint. Missing licensing is not permission.

### Exact artifact and current local identity

This review concerns only `hafizqaim/Workspace-Safety-Detection-using-YOLOv8`,
release `v1.0.0`, release ID `232751089`, asset ID `273300310`, `best.pt`,
**6,249,635 bytes**, SHA-256
**`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`**.
The [release metadata](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/232751089)
and [source download URL](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/download/v1.0.0/best.pt)
identify that asset. The [tag reference](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/ref/tags/v1.0.0)
still points to `da9e8a3f41b55e7cc3d6ce400528b0dba939ec33`.
GitHub reports `immutable: false`; pin the digest, not merely the tag or URL.

Read-only local `stat` and `shasum -a 256` checks confirm that the retained
regular file `models/best.pt` **currently matches this
Hafizqaim size and digest**, not Baskarmother. This supersedes earlier
statements about the current contents of that path; earlier Baskarmother
verification results remain historical observations of different bytes.
Hash agreement proves byte identity, not transfer history, training lineage,
safe deserialization or permission. The configured acquisition destination
remains `models/preferred-v1.0.0.pt`; no path or candidate was changed.

### Refreshed primary-source evidence

| Source and scope | Observed evidence | Rights/provenance limit |
| --- | --- | --- |
| [Repository metadata](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8), [release-tag tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/da9e8a3f41b55e7cc3d6ce400528b0dba939ec33?recursive=1), and [later source tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/8f16e157b0533e5ef62bb48ca829b612bad63d3b?recursive=1) | `license: null`; both trees are non-truncated and list no license file. Commit history still begins with head `8f16e157b0533e5ef62bb48ca829b612bad63d3b`. | API detection and file absence alone are not definitive legal conclusions, but no affirmative exact-weight grant is established. |
| [Tag README](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/da9e8a3f41b55e7cc3d6ce400528b0dba939ec33/README.md), [later README](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/README.md), and release body | READMEs invite download and running the inference script; release describes a trained YOLOv8n model and “PPE Detection v3 (Roboflow)”. Neither inspected README nor release body supplies explicit license terms for the weights. | Setup instructions are contextual evidence, not an accepted grant for internal commercial use, modification/fine-tuning or redistribution. No permissive weight license may be assigned by inference. |
| [Issue #1](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1) and [comments API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1/comments?per_page=100) | Open, zero comments; comments response empty. Existing question identifies this digest and asks about internal commercial evaluation, conversion, proprietary redistribution and upstream/data lineage. | No maintainer answer or permission. The existing question does **not explicitly ask about fine-tuning or rights to resulting weights**; those need separate explicit clarification. No inquiry was posted here. |
| [Space metadata](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection), [pinned mirror tree](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection/tree/c170c60a29a4eafed23055469e1ee15fad930243?recursive=true), and [pinned card](https://huggingface.co/spaces/hafizqaim/Workspace-Safety-Detection/blob/c170c60a29a4eafed23055469e1ee15fad930243/README.md) | Revision `c170c60a29a4eafed23055469e1ee15fad930243`; `best.pt` LFS size/digest match this release. Metadata has no card license; returned tree lists no license file; card provides setup/performance text rather than explicit weight terms. | Corroborates published byte identity, not additional permission. A public demo, ungated hosting or mirror is not a rights grant. |
| [Pinned notebook](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/workplace-safety.ipynb) and [commit history](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/commits?per_page=100) | Training command requests `model=yolov8n.pt`, 10 epochs and 640 image size; data YAML references `/kaggle/input/ppe-objection-detection/datasets/ppe detection.v3i.yolov8/`. Notebook was added at `e8b7834d68a14e5e806a29a1b3111b67c443d39d`, `2025-07-16T06:58:15Z`, after release publication at `06:49:08Z`. | No immutable initialization digest, exact training software/version, dataset owner/export identity, contributing rights or digest-bound training run. Chronology does not prove a different model, but cannot bind the later notebook to this release. |

The dataset title and Kaggle path are insufficient to identify a unique
provider/version and license. No license from a similarly named dataset or
another candidate is attributed to Hafizqaim. Dataset permission, even if
later established, would remain separate from exact-weight permission;
neither an MIT declaration on another model nor its CC BY dataset applies here.

### Upstream software and model terms are separate evidence layers

The [version-tagged Ultralytics 8.3.70 LICENSE](https://github.com/ultralytics/ultralytics/blob/v8.3.70/LICENSE)
contains AGPL version 3 terms. Section 2 affirms running the unmodified
Program and permits making/running non-conveyed covered works while the
license remains in force; output is covered only if its content constitutes
a covered work. Sections 4–6 address conveying covered works and associated
notices/source conditions. Section 13 requires a modified network-interactive
version to offer Corresponding Source to remote users. These conditional
terms must not be reduced to “every private PoC must publish everything” or
“local use is always exempt”. Whether this third-party checkpoint or a
fine-tuned derivative is a covered work remains a rights-review question.
The project's runtime version is not proof of the publisher's training stack.

Separately, the refreshed [official Ultralytics licensing guidance](https://www.ultralytics.com/license)
states that trained/fine-tuned models fall under AGPL by default and that
private internal business tools, non-open-source R&D and proprietary/commercial
fine-tuned deployments require Enterprise licensing rather than its stated
full-project open-source route. This is the **vendor's position**, not an
independent determination of Hafizqaim's exact-weight license or authority.
The [technical FAQ](https://docs.ultralytics.com/help/FAQ/)
describes training and deployment capabilities, not permission for these bytes.
Current unversioned guidance is not proof of terms accepted by the publisher
when training this release.

No executed Enterprise agreement or other upstream grant was supplied.
A potential agreement must be reviewed for actual entities, software/model
coverage, term and onward rights; it cannot automatically grant Hafizqaim's
or dataset contributors' rights. Enterprise procurement is not authorized
here and would not automatically meet the unchanged permissive-weight
requirement. No definitive AGPL inheritance or permissive eligibility is
asserted for this artifact.

### Intended PoC activities and permission status

| Activity requiring assessment | Evidence covering this exact digest | Present status / required clarification |
| --- | --- | --- |
| Retain/copy weights and perform local internal commercial evaluation/inference | Public release and README instructions; no accepted weight-specific terms | **Unresolved.** Obtain an affirmative grant covering the actual Renewi PoC entities and internal evaluation purpose; “PoC”, local execution or no charge is not an automatic exemption. |
| Fine-tune on authorized additional data, including adding negative vest; retain and use resulting checkpoints | No explicit publisher fine-tuning/modification grant or derivative-weight terms found | **Unresolved.** Confirm permission to modify/train from this initialization, ownership/license and use/sharing rights for resulting weights, and applicable upstream/software/data conditions. Adding a class would create a new artifact needing its own identity and validation. |
| Convert/export or optimize weights for another runtime | Existing issue asks about conversion but remains unanswered | **Unresolved.** Confirm adaptation/export scope and retained notices; conversion does not remove source-weight obligations. |
| Run a private API/demo, including authenticated or IP-restricted access | Publisher hosts a demo but grants no accepted downstream deployment rights | **Unresolved.** Specify users, legal entities, hosting and network access; assess applicable covered-work/network terms. Authentication/IP restrictions are not licensing exemptions. |
| Deliver code, containers, original or fine-tuned/exported weights to a customer, contractor or another entity | No accepted redistribution/onward grant or complete notice package | **Unresolved.** Confirm recipient and redistribution scope, source/notice obligations and permitted license of delivered material. Do not treat an internal trial as permission for later delivery. |

### Evidence needed to resolve the rights gate

1. **Publisher/rightsholder:** provide a durable statement identifying the
   release asset and full SHA-256, copyright holders and authority to grant
   rights. Explicitly cover copying, internal commercial PoC evaluation,
   fine-tuning/modification, conversion, use of resulting weights, network
   deployment and any permitted redistribution, with license text, notices
   and limitations. State which rights are not granted.
2. **Publisher and upstream rights holders where necessary:** identify the
   initialization asset/source/revision/digest, actual training software and
   version, exact dataset provider/version/export and contributing sources;
   explain the release-to-training-run linkage and applicable permissions.
   Establish any additional grant actually held, rather than assuming it.
3. **PoC/model owner:** document participating legal entities, internal and
   external users, local/network access, recipients, intended proprietary or
   disclosure posture and whether fine-tuning/export is contemplated.
4. **Designated rights reviewer:** assess the digest-bound publisher grant,
   authority, upstream/data obligations and actual intended activities.
   Record explicit acceptance or rejection, date, reviewer, evidence URLs,
   constraints and required notices. Silence is not acceptance.

Licensing alone cannot repair the separate recorded capability gap: the
[exact-release static taxonomy](#complete-observed-serialized-class-list)
has no explicit negative-vest class. Fine-tuning is neither authorized by
this review nor an approval of a hypothetical new checkpoint. Operational
verification, safe-loading clearance and model/replacement decisions remain
separate gates.

### Scope and focused validation

Only this source-adjacent evidence document is updated; no Spec Builder
artifact, generated research page or implementation plan is created or edited.
The existing read-only source checker
retrieved all eleven configured metadata/text sources; supplemental requests
read pinned READMEs, mirror metadata and the upstream license. Notebook JSON
and remote Python were inspected as inert text, never executed. Local checks
only measured file type/size and SHA-256. No dependencies were installed, no
weights/datasets were downloaded, no checkpoint was loaded or unpickled,
and **prediction/training calls: 0**. Tool stdout supplied the evidence; no
raw source report was persisted.

The outer workspace is not a Git repository, so a Git working-tree diff was
unavailable; direct file/configuration validation is used instead.
[`config/model.yaml`](../config/model.yaml) remains unchanged:
`approved`, `actual_classes_verified` and `required_classes_supported` are
false; reviewer/license fields are null. The retained checkpoint and
source-checking utility are untouched. **Exact-weight rights and DEC-01 remain
unresolved; implementation and inference remain paused.**

## DEC-01 Baskarmother replacement assessment — 2026-10-03

**Disposition: retain Baskarmother as a replacement evidence lead; do not
approve or substitute it. No inference is authorized by this assessment.**
The recorded implementation plan
requires investigation of weights-specific licensing, revision, architecture,
class list and actual Person/PPE support; an unsuitable original candidate
requires a documented and approved replacement before inference work.
Approval of plan revision 1 is not approval of any model.

The [original-candidate verification](#dec-01-original-candidate-verification--2026-10-03)
records four of five required labels and no explicit negative-vest class in
hafizqaim's exact-release serialized map. Baskarmother closes that particular
**serialized-label gap**, not the rights, architecture or operational gates.
The named keremberke fallback is not assumed to detect Person or either vest
class. Neither a fallback label nor this review priority authorizes substitution.

### Exact replacement artifact and evidence basis

Assess only `baskarmother/yolov8-ppe-construction`, revision
`3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`,
**6,258,474 bytes**, SHA-256
**`8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`**.
The [pinned weight source](https://huggingface.co/baskarmother/yolov8-ppe-construction/resolve/3213ed51de90cbc76e577e6944e84f7c74343526/best.pt)
and [revision-specific Hub metadata](https://huggingface.co/api/models/baskarmother/yolov8-ppe-construction/revision/3213ed51de90cbc76e577e6944e84f7c74343526?blobs=true)
identify the recorded source artifact. The
[local validation record](#uploaded-local-checkpoint-validation--2026-10-03)
reports that `models/best.pt` matches both size and
digest. Persistence is resolved; that historical match was not rerun here.
It proves byte identity, not training lineage, loading safety or rights.

This assessment consolidates recorded primary-source and local-verification
evidence, the plan, current configuration and inspection utility source.
Public sources were not re-fetched; no new publisher grant, architecture
attestation or runtime result is claimed. Historical sections below are
superseded only where the later fingerprint/serialized-label records supply
stronger evidence, not for their still-unresolved runtime and rights findings.

### DEC-01 requirement assessment

| Required investigation | Evidence and status | Unresolved acceptance gate |
| --- | --- | --- |
| Revision and weight identity | **Recorded exact-artifact match.** Pinned source revision, filename, size and SHA-256 are identified above; the retained local file matched them in the recorded verification. | Identity is sufficiently recorded for this assessment, but does not approve use. Any later authorized provisioning/loading must verify the same bytes. |
| Weights-specific licensing | **MIT-declared, not rights-approved.** The [pinned publisher card](https://huggingface.co/baskarmother/yolov8-ppe-construction/blob/3213ed51de90cbc76e577e6944e84f7c74343526/README.md) declares `license: mit`; inspected siblings contain no standalone LICENSE. | Exact-weight grant scope, publisher authority, complete notices, intended-use acceptance and applicable upstream obligations remain unresolved. Missing a LICENSE does not itself invalidate the declaration or prove prohibition. |
| Initialization and training lineage | **Publisher declarations only.** Card names `yolov8n`, 640×640 training, 100 epochs, SGD and the linked construction-safety dataset. Its pinned dataset documentation declares CC BY 4.0; project Ultralytics 8.3.70 is AGPL-3.0. | No immutable initialization digest, actual training-software identity, exact consumed dataset/export or complete contributing-source permissions are established. Dataset rights do not license weights; runtime terms are a separate layer. |
| YOLOv8 architecture | **Declared YOLOv8n; exact topology unverified.** Serialized Ultralytics `DetectionModel`/`Detect` references are consistent with the declared family, not architecture certification. | Trustworthy digest-bound architecture, tensor/output-head validity and class-count agreement with the runtime remain unverified. Similar size, references and literal `nc` fields cannot establish these properties. |
| Complete class list | **Verified at the recorded serialized-metadata level.** One complete 17-entry literal map, two literal `nc: 17` fields, and one uninterpreted nonliteral `nc` reference were observed. The [complete observed taxonomy](#complete-observed-serialized-taxonomy) lists IDs 0–16. | Complete runtime `model.names`, annotation semantics and head agreement remain unverified. Static label presence is not the application's `actual_classes_verified` acceptance decision. |
| Actual Person/PPE support | **Not demonstrated.** All five required names occur in the fingerprint-matched metadata, as detailed below. | No runtime detector, Person/PPE boxes, confidence values, Renewi accuracy or throughput results were obtained. Direct Person localization for FR-1 association and FR-2 bottom center is unverified. |
| Documented and approved replacement | **Assessment documented; approval absent.** Baskarmother is not configured or selected for implementation. | The PoC/model owner must record an explicit digest-bound replacement decision after required evidence and reviewer acceptance, with any necessary plan reapproval. No gate is satisfied by implication. |

The [exact-weight licensing review](#baskarmother-exact-weight-licensing-review)
separates MIT, dataset CC BY 4.0, runtime AGPL and Ultralytics' broader vendor
position. This assessment establishes neither definitive AGPL inheritance nor
unrestricted MIT eligibility for these third-party weights. A hypothetical
Enterprise agreement is not an executed grant covering this artifact and does
not automatically satisfy the unchanged permissive-weight requirement.

### Required classes: serialized coverage versus runtime support

| Canonical target | Recorded serialized ID / literal name | Coverage established | Demonstrated runtime support |
| --- | --- | --- | --- |
| `person` | 9 / `person` | Label present in exact bytes | Unverified; no observed direct Person boxes or usable bottom-center localization |
| `helmet` | 4 / `hardhat` | Label present; conditional normalization | Unverified; no observed helmet detections |
| `no_helmet` | 6 / `no-hardhat` | Explicit negative label present; conditional normalization | Unverified; no observed explicit negative-helmet detections |
| `safety_vest` | 12 / `safety vest` | Label present; conditional normalization | Unverified; no observed vest detections |
| `no_safety_vest` | 8 / `no-safety vest` | Explicit negative label present; conditional normalization | Unverified; no observed explicit negative-vest detections |

Thus **five of five required labels are serialized**, while **operational
five-class support is not established**. No runtime aliases were configured.
Negative-label box extent and semantics still require review. Absence of a
positive helmet/vest detection must never become an explicit negative;
insufficient or contradictory evidence must remain UNKNOWN.

The recorded restricted load used Torch 2.6.0 with `weights_only=True` and
refused `ultralytics.nn.tasks.DetectionModel` with `UnpicklingError`.
Runtime `model.names` was not obtained. That refusal is neither a maliciousness
finding nor proof of incompatibility with every reviewed loading path.
No unrestricted retry or model-class allow-list is authorized here.

### Unresolved gates and responsible owners

| Gate | Evidence/action required to resolve it | Responsible owner |
| --- | --- | --- |
| Intended-use weight rights | Digest-bound grant scope/authority and notices; initialization/software/data lineage and applicable obligations; recorded acceptance for actual entities, users, network access and recipients | Publisher/rightsholder, PoC/model owner and designated rights reviewer |
| Loading safety and exact architecture/taxonomy | Review and authorize a specific disposable least-privileged procedure; establish complete runtime names, topology/head agreement and annotation semantics for the same digest without unreviewed loading overrides | Security reviewer and model owner |
| Replacement approval before inference work | Record the selected artifact, accepted evidence, reviewer, date, constraints and explicit substitution decision; obtain any necessary plan reapproval. Separate evaluation authorization must also be explicit | PoC/model owner and plan approver where required |
| Operational Person/PPE evidence | After the preceding clearances and separate authorization, use reviewed, authorized image/video fixtures to record all five classes, confidences, original-coordinate boxes, input/frame identity, runtime and settings. The prior workspace scan found no Renewi media; no new inventory was run here | Renewi/evaluation owner and verification owner |
| Real-model FR-1 before FR-2 | Complete the plan's distinct AC-03 / VAL-03 application verification and explicit FR-1 pass before STEP-04. Label presence or a small detector smoke check cannot pass that application gate | Model/application owner and verification owner |
| Accuracy/runtime and evaluation acceptance | Identify the authoritative annotated 100-clip dataset, rights, split/overlap evidence and run provenance; agree numerical quality/runtime criteria before interpreting later measurements. A 5–10-input smoke trial is not this evaluation | Dataset owner, evaluation owner and PoC/model owner |

### Scope and focused validation of this assessment

Only this evidence document is updated. The read
[`config/model.yaml`](../config/model.yaml) still names hafizqaim; `approved`,
`actual_classes_verified` and `required_classes_supported` are false, and
reviewer/license fields are null. Those flags belong to the configured original
candidate, not to Baskarmother's separate serialized-label evidence.
The approved plan remains execution-blocked with STEP-01 failed and full
AC-01 / VAL-01 incomplete. No configuration, checkpoint, BRD, implementation,
generated research page or plan status is changed.

Seven inert parser self-checks passed using
`PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; sys.path.insert(0, "utils"); from inspect_ppe_candidates import self_test; self_test()'`
from the outer workspace root. They test metadata-parser rejection behavior,
not architecture, detection capability, rights or full VAL-01.
The local verifier was reviewed
but not rerun because it includes a restricted-load attempt; the
primary-source checker targets
hafizqaim, not Baskarmother, and was not rerun as replacement evidence.
No weights/datasets were downloaded, no checkpoint was loaded, no model
inference or accuracy evaluation ran, and **prediction calls for this assessment:
0**. **DEC-01 replacement approval remains unresolved; implementation and
inference remain paused.**

## DEC-01 original-candidate verification — 2026-10-03

**Outcome: do not approve the original candidate for the unchanged five-class
contract. No replacement is approved and no inference is authorized.** This
verification addresses `hafizqaim/Workspace-Safety-Detection-using-YOLOv8`
first. It supersedes earlier “not downloaded” and “checkpoint classes
unverified” statements **only for the fingerprint and literal serialized
taxonomy of this exact release**. Those earlier sections remain historical.
Runtime classes, architecture/head validity, detection capability and rights
acceptance are not established by static inspection.

### Exact artifact and evidence levels

Primary-source refresh began at **2026-10-03 12:11:17 UTC**. All eleven
bounded metadata/text requests returned evidence. A preceding inline shell
request failed parsing before network execution; the successful retry used the
read-only source checker.

| Subject | Verified observation | Limit or unresolved claim |
| --- | --- | --- |
| Revision | `v1.0.0` tag references commit `da9e8a3f41b55e7cc3d6ce400528b0dba939ec33`; inspected later source tree is `8f16e157b0533e5ef62bb48ca829b612bad63d3b` | GitHub reports release `232751089` as `immutable: false`; tag/URL alone cannot guarantee unchanged bytes |
| Release weights | Asset `273300310`, `best.pt`, **6,249,635 bytes** | Downloaded into bounded memory for research; no new checkpoint file retained |
| Fingerprint | Computed SHA-256 **`5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`**; size and hash both match refreshed release metadata | Identifies inspected bytes, not safe loading, training lineage or permission |
| Architecture | Release declares YOLOv8n; notebook requests training with `model=yolov8n.pt` | Exact model topology, tensors, output head and pinned-runtime compatibility remain unverified; no model object reconstructed |
| Taxonomy | One complete literal **17-class** map in `best/data.pkl`; two literal `nc` values equal **17** | One nonliteral `nc` reference remains uninterpreted; these are serialized fields, not printed runtime `model.names` |
| Weight-specific licensing | Repository API reports `license: null`; both non-truncated inspected source trees contain no license file; release body supplies no grant | No accepted exact-weight permission found. Missing a license file is not itself a legal determination of prohibition |
| Maintainer clarification | Issue #1 remains open, reports zero comments, and comments response is empty | An unanswered permission request is not a grant or publisher attestation |
| Mirror | Space revision `c170c60a29a4eafed23055469e1ee15fad930243` has no card license or listed license file | Public hosting and mirror metadata do not resolve weights rights |
| Training lineage | Notebook references Kaggle path `ppe-objection-detection/datasets/ppe detection.v3i.yolov8`; release names Roboflow PPE Detection v3 | Exact provider/export, data rights, initialization digest, training history and link to this checkpoint remain unresolved |

The notebook was added at commit
`e8b7834d68a14e5e806a29a1b3111b67c443d39d`, timestamp
`2025-07-16T06:58:15Z`, after release publication at `06:49:08Z`.
Its ordered labels match the newly inspected serialized map. That agreement
corroborates the taxonomy; it does not establish a digest-bound training run.

### Complete observed serialized class list

| ID | Literal raw name |
| --- | --- |
| 0 | `Barefoots` |
| 1 | `Ear-protection` |
| 2 | `Harness` |
| 3 | `No_Ear-Protection` |
| 4 | `No_Glasses` |
| 5 | `Sandals` |
| 6 | `boots` |
| 7 | `face_mask` |
| 8 | `face_nomask` |
| 9 | `glasses` |
| 10 | `hand_glove` |
| 11 | `hand_noglove` |
| 12 | `head_helmet` |
| 13 | `head_nohelmet` |
| 14 | `person` |
| 15 | `shoes` |
| 16 | `vest` |

| Required target | Exact-release serialized evidence | Actual detection support |
| --- | --- | --- |
| Person | ID 14 / `person` present | Unverified; no boxes or confidences observed |
| Helmet | ID 12 / `head_helmet` present; conditional normalization to `helmet` | Unverified |
| Explicit no-helmet | ID 13 / `head_nohelmet` present; conditional normalization to `no_helmet` | Unverified |
| Safety vest | ID 16 / `vest` present; conditional normalization to `safety_vest` | Unverified |
| Explicit no-safety-vest | **Absent from the complete extracted literal map** | No supported explicit-negative-vest class; runtime/head behavior not tested |

The source demo filters predictions to `classes=[12, 16]`. It therefore does
not demonstrate Person or negative-helmet outputs, but the filter does not
prove those classes absent from the underlying checkpoint. Person label
presence does not demonstrate usable Person boxes for FR-1 association or
FR-2 bottom-center localization.

The candidate has static label evidence for **four of five required targets**,
not operational five-class support. No name mapping can create a missing
negative-vest class. Missing a positive vest detection must never be converted
into `no_safety_vest`; insufficient or conflicting evidence must remain UNKNOWN.

### Reproduction and focused validation

Commands executed from the outer workspace root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 utils/inspect_hafizqaim_checkpoint.py
PYTHONDONTWRITEBYTECODE=1 python3 utils/check_dec01_primary_sources.py
PYTHONDONTWRITEBYTECODE=1 python3 -c 'import sys; sys.path.insert(0,"utils"); from inspect_ppe_candidates import self_test; self_test()'
```

The checkpoint inspector observed **363 ZIP members**, one metadata member
`best/data.pkl` of **95,730 bytes**, and **37,805 inert pickle opcodes**.
The names map spans offsets **88479–88862**; literal `nc` keys are at
**86745** and **87232**; the uninterpreted `nc` reference is at **88393**.
The seven parser checks passed. Evidence was collected from tool stdout,
not an existing saved raw report. These checks are not detection tests,
architecture certification, deserialization-safety certification or rights approval.

No Torch/Ultralytics model import, unpickling, restricted/unrestricted model
load, remote notebook execution, dataset download or inference was performed
in this verification. **Prediction calls: 0.** The bounded research inspection
did not invoke or bypass the application's acquisition approval controls.
The existing `models/best.pt` belongs to the separate Baskarmother evidence
record; it was not treated as the original candidate or inspected here.

### Suitability and approval gaps

1. **Capability gap:** this exact release's extracted taxonomy does not provide
   explicit negative vest. Under the unchanged contract it is not an eligible
   five-class choice on current evidence. Publisher clarification may explain
   semantics or provide contrary artifact-bound evidence, but cannot create a
   missing output class by assertion or renaming.
2. **Rights gap:** the publisher/rightsholder must provide a grant bound to this
   digest covering intended use, authority/notices, initialization and training
   lineage, and applicable upstream/data obligations. The designated rights
   reviewer must explicitly accept those rights.
3. **Operational evidence gap:** exact architecture/head agreement, complete
   runtime taxonomy, annotation semantics and working Person/PPE outputs remain
   unverified. Any later loading needs separately reviewed safety authorization;
   this report does not start that work.
4. **Replacement approval gap:** if retaining the five-class requirement, the
   model owner must document an eligible replacement and explicit approval
   before inference work. Baskarmother's separately verified serialized labels
   do not approve substitution or resolve its rights/loading gaps.

The named keremberke fallback is **not assumed to detect Person**: its recorded
published taxonomy also omits both vest classes, and its exact-checkpoint
operational support and weight rights remain unverified. That prior fallback
record was reviewed, not re-fetched or re-inspected here.

**DEC-01 remains unresolved; implementation/inference remain paused.**
`config/model.yaml` still names hafizqaim, with `approved`,
`actual_classes_verified` and `required_classes_supported` false and reviewer/
license fields null. The latter flags are unchanged acceptance controls, not a
denial of the newly established literal-label evidence. No configuration, BRD,
application implementation, replacement decision or plan status was changed.

### Primary-source references

- [Repository metadata](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8), [release metadata](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/232751089), and [tag reference](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/ref/tags/v1.0.0).
- [Release-tag tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/da9e8a3f41b55e7cc3d6ce400528b0dba939ec33?recursive=1) and [later inspected tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/8f16e157b0533e5ef62bb48ca829b612bad63d3b?recursive=1).
- [Pinned notebook](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/workplace-safety.ipynb), [commit history](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/commits?per_page=100), and [pinned demo source](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/inference.py).
- [Existing issue #1](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1), [comments API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1/comments?per_page=100), and [Space metadata](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection).
- [Inspected release download](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/download/v1.0.0/best.pt) and existing inert checkpoint inspector.

## Uploaded local checkpoint validation — 2026-10-03

The user reported that `best.pt` is now in `models`. Local verification began at **2026-10-03 11:04:18 UTC**, with the corrected restricted-loader run beginning at **11:05:08 UTC**. **Checkpoint persistence is now resolved:** the regular, nonsymlink file at the outer workspace's `models/best.pt` exists and matches the expected Baskarmother artifact exactly. This section supersedes the earlier attempt's persistence blocker and workspace inventory, not its historical observations or unresolved safety/rights findings.

### Local identity and static class evidence

| Check | Observed result |
| --- | --- |
| Local checkpoint | `models/best.pt`, retained; not downloaded again or rewritten |
| Size | **6,258,474 bytes**, expected-size match |
| SHA-256 | **`8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`**, expected-digest match |
| Reference identity | `baskarmother/yolov8-ppe-construction`, pinned revision `3213ed51de90cbc76e577e6944e84f7c74343526` |
| Static inspection | `best/data.pkl`, **104,137 bytes**, **38,859** inert pickle opcodes |
| Taxonomy | One complete literal map with **17** entries; two literal `nc` values of **17**; one nonliteral `nc` reference remains uninterpreted |
| Parser checks | **7 passed**, including malformed/nonliteral metadata rejection |

Hash agreement identifies the uploaded bytes with the recorded pinned artifact; it does not establish the user's transfer history, safe deserialization, training lineage or accepted rights. The complete 17-label map reproduced from this local file is identical to the map recorded in the earlier attempt below.

| Requested target | Local serialized ID / literal name | Serialized match | Runtime names / Renewi detections |
| --- | --- | --- | --- |
| Person | 9 / `person` | Yes | Not obtained / not measured |
| Hardhat | 4 / `hardhat` | Yes | Not obtained / not measured |
| No-hardhat | 6 / `no-hardhat` | Yes | Not obtained / not measured |
| Safety vest | 12 / `safety vest` | Yes | Not obtained / not measured |
| No-safety vest | 8 / `no-safety vest` | Yes | Not obtained / not measured |

These are **serialized labels, not printed runtime `model.names` or demonstrated detections**. No negative PPE class was inferred from absence of a positive detection.

### Restricted loading and environment

The existing environment reports **Python 3.11.14, Torch 2.6.0, Ultralytics 8.3.70 and opencv-python 4.11.0.86**, on **Darwin arm64**. Package versions were read from installed metadata; no dependencies were installed or upgraded and no Ultralytics detector was imported or instantiated.

The first utility run conservatively stopped before loading because `get_safe_globals()` was nonempty. A read-only fresh-process check identified exactly Torch's import-time nested-tensor registrations, `torch.nested._internal.nested_tensor.NestedTensor` and `_rebuild_njt`. The utility preflight was corrected to recognize those exact framework objects and reject any other registry contents; **the registry itself was neither cleared nor expanded**.

The corrected run verified the fingerprint again, found **16** globals not default-allow-listed in Torch's static scan, and attempted only:

```python
torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)
```

Observed result: **`UnpicklingError`**, with:

```text
WeightsUnpickler error: Unsupported global: GLOBAL ultralytics.nn.tasks.DetectionModel was not an allowed global by default.
```

The static global scan is not a safety certification or evidence of maliciousness. No `weights_only=False`, model-class allow-list, loading override, `YOLO(...)` invocation or fallback loading path was used. Runtime taxonomy, tensor/head validity and inference compatibility remain unverified; this refusal does not prove incompatibility with every reviewed loading path.

### Media inventory and focused verification

A recursive workspace scan excluding `.venv`, `.git`, `skills`, `node_modules` and `__pycache__` found **zero image, video or ZIP candidates**, with **no scan errors**. Extensions checked were `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`, `.mpeg`, `.mpg` and `.zip`. Checkpoint-suffix paths were `models/best.pt` and `models/._best.pt`; only the explicitly requested `models/best.pt` was inspected or passed to the restricted loader. No external Renewi manifest or media path was supplied.

**Renewi inputs processed: 0; prediction calls: 0.** No confidence scores, bounding boxes, accuracy or latency results were produced. “Not measured” is not a zero confidence or failed-class result. Unrelated/public/synthetic images were not substituted.

Reproducible local command from the outer workspace root:

```sh
PYTHONDONTWRITEBYTECODE=1 ./Renewi_EHS_Lighthouse/.venv/bin/python utils/verify_local_ppe_checkpoint.py
```

The new local-only verification utility reads bounded local bytes, uses the existing inert parser, inventories candidate media paths and refuses unsafe fallback loading. The corrected run reports `restricted_load_status: blocked` and exits with status 2 by design; fingerprint/static success is not overall validation success.

The existing downloader safeguard regression suite also ran from the nested application root:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest backend/tests/test_download_model.py -q -p no:cacheprovider
```

Result: **25 passed in 1.97 s**. These tests verify acquisition tooling safeguards, not this model's detection capability or rights. No approval controls were changed.

### Remaining blockers and resolution

1. **Safe runtime loading:** the security/model owner must review and authorize a specific disposable, least-privileged loading procedure for this exact digest. The current host/virtual environment is not a security sandbox. No reviewed sandbox procedure was supplied, so unrestricted reconstruction or model-class allow-list expansion cannot safely proceed here.
2. **Renewi media:** the Renewi/evaluation owner must provide accessible, authorized paths or a manifest for **5–10 representative images/clips**, with positive/negative helmet and vest examples and reviewed expected observations. Annotations are required for accuracy claims.
3. **Rights/provenance:** the existing [exact-weight licensing review](#baskarmother-exact-weight-licensing-review) was read; public sources were not re-fetched in this invocation. Its **MIT-declared, not rights-approved** outcome remains unchanged. The publisher/rightsholder must supply digest-bound grant scope/authority, notices and initialization/training-data lineage; the designated rights reviewer must accept intended-use and upstream/data obligations. Uploading or hashing the file does not resolve these questions.

Once those prerequisites are satisfied, resume complete runtime `model.names` inspection and the requested Renewi smoke trial, recording input/frame identity, settings, class, confidence and original-coordinate boxes. The separate authoritative 100-clip evaluation and agreed numerical acceptance criteria remain outstanding; a small smoke trial cannot replace them.

**Decision unchanged: no model approved; implementation remains paused.** Only this evidence document and the local verification utility were changed. The checkpoint, BRD, application code, configured hafizqaim candidate, false approval/capability flags and implementation plan were untouched.

## Actual-checkpoint validation attempt — 2026-10-03

This section records the earlier user-requested validation of `baskarmother/yolov8-ppe-construction`. Primary-source checks began at **2026-10-03 10:35:29 UTC**. The user requested download, actual checkpoint loading, printing `model.names`, five-class verification, inference on 5–10 Renewi images/clips, confidence records and license/provenance review. **The validation is incomplete:** exact bytes and serialized five-label coverage were independently reproduced, but restricted loading failed and no Renewi media was available. No operational detections or confidence values were produced.

This request authorizes this bounded validation attempt, not adoption or implementation. Earlier sections' statements that no acquisition or inspection occurred describe their historical invocations; they do not describe this attempt. Earlier supplied static findings now have independently reproduced evidence at the static-metadata level only. No BRD, application code, model configuration, approval flag or implementation plan was changed.

### Artifact acquisition and independently observed identity

| Field | Observed evidence |
| --- | --- |
| Repository | `baskarmother/yolov8-ppe-construction` |
| Pinned revision | `3213ed51de90cbc76e577e6944e84f7c74343526` |
| Source | [Pinned best.pt](https://huggingface.co/baskarmother/yolov8-ppe-construction/resolve/3213ed51de90cbc76e577e6944e84f7c74343526/best.pt) |
| Downloaded byte count | **6,258,474**, matching pinned Hub metadata |
| Computed SHA-256 | **`8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`**, matching pinned Hub LFS metadata |
| Retained local checkpoint | **None.** Two binary-download tool attempts to `assets/model-inspection/baskarmother-3213ed51-best.pt` failed with `RLE RleMessageType.FS_WRITE failed: connection lost`; a subsequent existence check returned false |
| Successful acquisition | Existing inspection utility downloaded bounded checkpoint bytes into memory; the restricted-load attempt independently fetched and fingerprint-checked bytes in memory |

The download failures were file-persistence/tool failures, not evidence that the public weight URL was unavailable. No shell file-writing workaround, application downloader gate bypass, configuration substitution or approval toggle was used.

### Complete observed serialized taxonomy

The existing static inspection utility ran from the outer workspace root:

```sh
PYTHONDONTWRITEBYTECODE=1 ./Renewi_EHS_Lighthouse/.venv/bin/python utils/inspect_ppe_candidates.py --self-test baskarmother
```

Observed output: `SELF_TEST: 7 parser checks passed; no unpickling`; both fingerprint checks true; **38,859** pickle opcodes; member `best/data.pkl`, **104,137 bytes**. One literal names map contained 17 entries, and two literal `nc` fields each reported **17**. One nonliteral `nc` reference remained uninterpreted. These are parser observations, not tensor/head or object-graph validation.

```json
{
  "0": "barricade",
  "1": "dumpster",
  "2": "excavators",
  "3": "gloves",
  "4": "hardhat",
  "5": "mask",
  "6": "no-hardhat",
  "7": "no-mask",
  "8": "no-safety vest",
  "9": "person",
  "10": "safety net",
  "11": "safety shoes",
  "12": "safety vest",
  "13": "dump truck",
  "14": "mini-van",
  "15": "truck",
  "16": "wheel loader"
}
```

**This is actual-checkpoint serialized metadata, not printed runtime `model.names`.** All five required labels are present in the fingerprint-matched bytes. Operational class coverage, annotation semantics and usable outputs remain unverified.

### Actual restricted-load attempt and execution prerequisites

The existing environment successfully imported Torch and OpenCV. Observed versions: **Python 3.11.14, Torch 2.6.0, Ultralytics package 8.3.70 and OpenCV 4.11.0** (repository requirement `opencv-python==4.11.0.86`); host **Darwin arm64**. Ultralytics version/license were read from installed package metadata, not inferred from a model load. Global Python 3.14.7 lacked the model packages, but the existing project environment supplied the needed imports, so no packages were installed or upgraded. Pip also emitted invalid-distribution warnings; those warnings did not prevent the observed Torch/OpenCV imports.

After verifying size and SHA-256 again, the attempt called `torch.serialization.get_unsafe_globals_in_checkpoint(io.BytesIO(data))`, then **`torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)`**. The static global scan returned 16 globals not allow-listed by default, including `ultralytics.nn.tasks.DetectionModel` and `ultralytics.nn.modules.head.Detect`. That scan is not a safety certification or evidence of maliciousness.

The actual load raised `_pickle.UnpicklingError`:

```text
Weights only load failed.
WeightsUnpickler error: Unsupported global: GLOBAL ultralytics.nn.tasks.DetectionModel was not an allowed global by default.
```

No unrestricted `weights_only=False` retry, blanket safe-global allow-list, security override or package upgrade was made. The checkpoint was not reconstructed into a runtime detector, `YOLO(...)` was not invoked and **runtime `model.names` could not be printed**. This proves restricted-load refusal under the installed defaults, not that the checkpoint is incompatible with every supported loading path. A reviewed loading procedure in a disposable least-privileged sandbox remains necessary; dependency isolation alone is not a security sandbox.

### Renewi media and detection/confidence record

A recursive workspace inventory, excluding `.venv`, `.git`, `skills` and `node_modules`, found **zero checkpoint files, images, videos or ZIP attachments** matching `.pt`, `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`, `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`, `.mpeg`, `.mpg` or `.zip`. Dependency sample images found in the initial unfiltered inventory were not Renewi media and were not used. No external Renewi media location or supplied clip manifest was identified for this request. This observation is limited to the workspace, not a claim that Renewi footage does not exist elsewhere.

| Requested target | Checkpoint ID / literal name | Serialized label present | Renewi detections / confidence |
| --- | --- | --- | --- |
| Person | 9 / `person` | Yes | **Not measured — no inference** |
| Hardhat | 4 / `hardhat` | Yes | **Not measured — no inference** |
| No-hardhat | 6 / `no-hardhat` | Yes | **Not measured — no inference** |
| Safety vest | 12 / `safety vest` | Yes | **Not measured — no inference** |
| No-safety vest | 8 / `no-safety vest` | Yes | **Not measured — no inference** |

**Renewi inputs processed: 0; prediction calls: 0.** No per-image/frame predictions, boxes, confidence scores, accuracy metrics or latency measurements exist for this attempt. “Not measured” must not be interpreted as zero detections, a confidence of zero, or a failed class. Missing positive PPE detections were not converted into negative labels. No unrelated public images, synthetic fixtures or publisher metrics were substituted for the requested 5–10 Renewi inputs.

### Refreshed license and provenance evidence

The [revision-specific model API with blobs](https://huggingface.co/api/models/baskarmother/yolov8-ppe-construction/revision/3213ed51de90cbc76e577e6944e84f7c74343526?blobs=true) and [pinned publisher card](https://huggingface.co/baskarmother/yolov8-ppe-construction/blob/3213ed51de90cbc76e577e6944e84f7c74343526/README.md) were retrieved successfully. They confirm the revision, published size/digest, **`license: mit`**, and repository files `.gitattributes`, `README.md` and `best.pt`; no standalone LICENSE is listed. The card declares base model `yolov8n`, the linked construction-safety dataset, 640×640 training, 100 epochs and SGD. These are publisher declarations, not independently verified training history.

The [pinned dataset export notice](https://huggingface.co/datasets/keremberke/construction-safety-object-detection/blob/a19eace121442bce60da9f5036dc16bf9f2f6fa6/README.dataset.txt) was re-read. It declares **CC BY 4.0**, links Roboflow Construction Site Safety, and lists two YouTube sources and seven cloned image collections. It does not establish contributor authority or exact checkpoint training membership. Dataset permission is separate from weight permission. Installed Ultralytics metadata reports **AGPL-3.0**, separate from the publisher's MIT declaration.

**Licensing outcome: MIT-declared, not rights-approved.** The checked sources do not supply digest-bound grant scope/authority, complete MIT notices, immutable initialization identity, exact training lineage or reconciled upstream obligations. This attempt does not make a legal determination about checkpoint license inheritance. The [existing exact-weight licensing review](#baskarmother-exact-weight-licensing-review) remains relevant; successful hashing and static class inspection resolve neither rights nor safe loading.

### Remaining blockers and owner actions

1. **Media:** the Renewi/evaluation owner must provide an accessible, authorized manifest or paths for 5–10 representative Renewi images/clips. Include explicit positive/negative helmet/vest cases and reviewed expected observations; annotations are needed for accuracy claims.
2. **Loading safety:** the security/model owner must review and authorize a specific sandboxed loading procedure for this object-based checkpoint. The observed restricted-load refusal must not be bypassed with an unreviewed unrestricted load or blanket allow-list.
3. **Checkpoint persistence:** restore the binary-download tool's file-write connection, or have the owner provision the reviewed pinned checkpoint through an approved transfer. Verify the same size/SHA-256 before loading.
4. **Rights:** the publisher/rightsholder and designated rights reviewer must resolve intended-use weight permission, publisher authority and upstream/data obligations. The bounded validation request is not a rights-acceptance decision.

Once these prerequisites are met, complete runtime `model.names` inspection and the requested 5–10-input predictions, recording each image or sampled clip frame, settings, class, confidence and original-coordinate box. A successful small smoke trial would still not establish AP/recall, full FR-1/FR-2 application correctness, the required 100-clip evaluation or adoption approval.

**Decision unchanged: no model approved; implementation remains paused.** This attempt changes only this evidence document. The configured hafizqaim candidate and false approval/capability flags are untouched. No BRD edits or coding-agent direction were issued.

## What data was Baskarmother tested on?

**Confirmed evaluation data for the exact checkpoint is not established by the inspected public sources.** The [pinned model card](https://huggingface.co/baskarmother/yolov8-ppe-construction/blob/3213ed51de90cbc76e577e6944e84f7c74343526/README.md) names [keremberke/construction-safety-object-detection](https://huggingface.co/datasets/keremberke/construction-safety-object-detection) under Training Details, but publishes no validation/test results or digest-bound evaluation record. This is a declared training dataset, not proof that its test split evaluated revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`.

You can [browse the linked Roboflow version-1 images](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety/dataset/1/images). The [pinned dataset card](https://huggingface.co/datasets/keremberke/construction-safety-object-detection/blob/a19eace121442bce60da9f5036dc16bf9f2f6fa6/README.md) reports 398 images with COCO annotations and 17 classes, including Person and all four required PPE labels.

| Available full dataset split | Reported images | Pinned data link |
| --- | --- | --- |
| Training | 307 | [train.zip](https://huggingface.co/datasets/keremberke/construction-safety-object-detection/resolve/a19eace121442bce60da9f5036dc16bf9f2f6fa6/data/train.zip) |
| Validation | 57 | [valid.zip](https://huggingface.co/datasets/keremberke/construction-safety-object-detection/resolve/a19eace121442bce60da9f5036dc16bf9f2f6fa6/data/valid.zip) |
| Test | 34 | [test.zip](https://huggingface.co/datasets/keremberke/construction-safety-object-detection/resolve/a19eace121442bce60da9f5036dc16bf9f2f6fa6/data/test.zip) |

Archive paths were confirmed in pinned repository metadata; their contents were not downloaded or audited. The loader's `full` configuration uses separate archives, but its `mini` configuration reuses `valid-mini.zip` for all three split names and is not an independent holdout arrangement. Distinct full archives alone do not establish source-level independence or absence of leakage.

Exact training revision/image membership, checkpoint selection on validation data, use and held-out status of the test split, split-generation procedure, source grouping, per-class support and exact-checkpoint metrics remain unavailable in the inspected evidence. The dataset's CC BY 4.0 declaration and contributing-source notice do not establish all source permissions or weight rights. Other construction-dataset versions and successor-model results must not be attributed to this artifact.

The detailed dataset/evaluation investigation records primary sources and evidence limits. Establishing actual testing would require a publisher run record tying the weight digest to a dataset/version, evaluated image manifest, split role, settings and results. No local inference or accuracy evaluation has occurred; static class inspection is not testing. This dataset does not replace the still-unidentified required 100-clip evaluation. No model approval, configuration change or implementation resumption is authorized.

STEP-01 establishes tooling, not permission to use publicly hosted weights.
STEP-02 must not begin until model approval is resolved. FR-2 remains blocked
until real-model FR-1 verification passes in STEP-03.

## Provisional Baskarmother choice, accuracy and adoption criteria

This clarification follows the authoritative requirements attachment. “Provisional choice” means prioritized for evidence review and, only after separate clearance, evaluation. It does not mean configured, selected for implementation or approved for adoption. The configured candidate remains hafizqaim and its approval/capability flags remain false.

### Why this candidate is provisional

The candidate is `baskarmother/yolov8-ppe-construction`, revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. Supplied prior fingerprint-verified static inspection reports `person`, `hardhat`, `no-hardhat`, `safety vest` and `no-safety vest`. Those labels align conditionally with the five required canonical classes. The declared YOLOv8n architecture, MIT metadata and comparatively explicit linked dataset documentation make it a useful first review lead. They do not establish accepted exact-weight rights, valid output heads, safe loading, usable detections or superior accuracy.

No operational evaluation has occurred. The static finding is attributed to the supplied prior evidence, not reproduced here. The inspection utility checks artifact identity and inert serialized metadata; it is not a runtime detector or accuracy evaluator. Licensing scope, publisher authority, initialization and training-data lineage, and applicable upstream obligations remain unresolved.

### Validate the detector for the specific tasks

After rights and loading-safety clearance and separate authorization, FR-1 model evidence must demonstrate actual Person boxes and correct positive and explicit negative helmet/vest detections on reviewed, annotated images and sampled video. Confirm the exact artifact's complete runtime taxonomy, architecture/head agreement, annotation semantics, coordinate conventions and compatibility with the pinned local environment. Observing one example of each class is a capability smoke check, not an accuracy result.

Representative evaluation should cover the intended camera views, lighting, distances, PPE appearances, occlusion, partial bodies and overlapping people. These are recommended coverage dimensions, not coverage already established. For FR-2, scrutinize Person misses and box-bottom localization near zone boundaries: the detector supplies boxes, not restricted-zone decisions. A Person label alone is insufficient, and a box cannot be invented when detection fails.

Keep the verification layers separate:

| Layer | Evidence needed | What a pass does not prove |
| --- | --- | --- |
| Model evaluation | Annotated comparisons of the exact detector's classes, confidences and boxes; measured local runtime behavior | Correct application mapping, PPE association, compliance rules or polygon processing |
| FR-1 application verification | Normalized outputs and frame IDs, configurable mappings, PPE-center-within-Person association with deterministic overlap handling, and all five compliance states | That real detector predictions are accurate on representative footage |
| FR-2 application verification | Clip-specific configured polygons, Person bottom center `((x1 + x2) / 2, y2)`, ray casting in matching coordinates, documented edge/corner policy and structured incursion events | That people are detected reliably or their box bottoms are sufficiently accurate |
| End-to-end task evaluation | Annotated real clips processed through the detector and application, including false/missed compliance outcomes and incursions | Accepted licensing or application security |

The application must distinguish COMPLIANT, HELMET_MISSING, VEST_MISSING, HELMET_AND_VEST_MISSING and UNKNOWN. Missing a positive PPE detection must never be treated as an explicit negative detection; insufficient or contradictory evidence must remain UNKNOWN. Geometry checks must cover inside, outside, boundary, corner and concave polygons if supported. Synthetic rule/geometry checks and real-model clip evaluation are complementary, not interchangeable. These application modules are not currently implemented.

### Measure accuracy reproducibly

Use the [representative held-out evaluation methodology](#representative-held-out-evaluation-methodology) below for annotations, source-level split isolation, matching, metric definitions, runtime measurements and acceptance interpretation. Detection AP50/precision/recall, person-level compliance outcomes and FR-2 incursion outcomes answer different questions and must have separate records. No measured accuracy or runtime result exists for this candidate here.

### What must pass before adoption

Adoption requires separate evidence for accepted exact-artifact rights and upstream/data obligations; trustworthy YOLOv8 architecture, complete taxonomy and semantics; safe authorized loading and pinned-runtime compatibility; real-model direct Person and all four PPE outputs; and reproducible accuracy/runtime results meeting pre-agreed criteria. The full FR-1/FR-2 PoC also requires passing application mapping, ingestion, association, compliance and zone verification, followed by end-to-end evidence. FR-2 remains contingent on real-model FR-1 verification.

The attachment supplies no numerical minimum mAP50, class recall, false-alarm/UNKNOWN rate or latency budget. The PoC/model owner and evaluation owner must document those targets before interpreting evaluation results. Its illustrative confidence, image-size and FPS settings are not acceptance thresholds. Without agreed targets, a completed evaluation can report measurements but cannot establish a quantitative acceptance pass.

The public 100-clip evaluation and provenance requirement must be satisfied rather than replaced with publisher scores. Basic authentication and the IP allow-list remain separate application/security acceptance responsibilities, not checkpoint capabilities or licensing exemptions. Finally, the responsible owner must record an explicit adoption decision and any required substitution approval; no metric, successful load or test pass grants adoption by implication.

Present status: rights acceptance, operational model results, authoritative dataset, numerical targets and application verification remain outstanding. This clarification executes no inspection, download, model load, inference, evaluation or tests, approves no candidate, and creates no implementation plan.

## Current model options against FR-1 and FR-2

This assessment uses the authoritative attachment for this request, the supplied fingerprint-verified checkpoint findings, and the recorded licensing review. It supersedes earlier statements below that checkpoint labels had not yet been inspected, but only at the static-metadata evidence level. Earlier sections retain their historical investigation context. No inspection, download, unpickling, inference, evaluation or test run was repeated for this assessment.

### Baskarmother versus Hansung Cho: present evaluation priority

**No best-performing model is established. Baskarmother is the conditionally preferred first evidence-review lead for a possible later PoC evaluation, not a selected or approved model.** This priority is supported by its more explicit linked dataset documentation and coherent numeric taxonomy, rather than demonstrated detection accuracy. If the deciding criterion is availability of publisher-saved validation detail, Hansung has the stronger documentary evidence on that narrower dimension; neither advantage establishes overall PoC suitability.

The supplied fingerprint-verified static findings confirm literal serialized presence of all five required labels in both exact candidate artifacts. That gives neither a class-coverage advantage at this evidence level. It does not validate output heads, observed Person/PPE boxes, safe loading, architecture or operational performance. Earlier statements below about unverified checkpoint names describe the prior public-text stage and are superseded only for static label presence.

Baskarmother's card gives numeric labels corroborated by pinned dataset documentation, including a dataset version and CC BY 4.0 declarations. This makes the next lineage review better grounded, but does not prove that the declared dataset trained the artifact, establish contributor rights, or license the weights. Hansung supplies training YAML and saved notebook validation, but the training dataset's exact provider/version/rights remain unidentified and the notebook's overall mAP50 0.750 differs from the card's 0.744. The reported run is not bound to the Hub digest; neither figure is a comparable Renewi result.

Both declare MIT, but exact-weight grant scope and authority, upstream obligations and training lineage remain unresolved. Neither has verified local compatibility, latency/throughput or a common representative PoC evaluation. Consequently, Baskarmother should be first only for targeted documentary follow-up; actual evaluation remains contingent on accepted rights, safety review and separate authorization. Hansung remains a parallel alternative and could become the first eligible evaluation candidate if it resolves those gates sooner. No inference or evaluation is authorized by this ordering.

A performance choice requires evaluation of eligible artifacts on the same reviewed, licensed, annotated representative PoC data, with documented settings and hardware and pre-agreed acceptance criteria. Compare the five required classes' AP50, precision and recall, especially Person and explicit negative PPE, alongside person-level compliance/zone outcomes and local runtime measurements. The required 100-clip evaluation dataset remains unidentified. Publisher image-dataset metrics cannot decide this comparison.

This recommendation uses existing records and supplied findings only; no inspection, download, model load, inference, tests or evaluation was repeated. The configured preferred model, false approval/capability flags and implementation pause remain unchanged. The conclusion is an evidence-based review priority, not an accuracy winner or adoption decision.

**Four alternatives have static evidence of the complete five-label set: Baskarmother, Hansung Cho, SafetyVision v2 and Snehil Sanyal. None has established full FR-1/FR-2 readiness or accepted exact-weight rights.** The required set is `person`, `helmet`, `no_helmet`, `safety_vest` and `no_safety_vest`: four PPE classes plus Person. A complete label set is a necessary prerequisite, not a demonstrated real-time safety solution.

### Conditional candidate comparison

| Candidate and inspected artifact | Supplied checkpoint finding | Licensing position | Conditional fit for the unchanged requirements |
| --- | --- | --- | --- |
| `baskarmother/yolov8-ppe-construction`, pinned `best.pt` | All five labels, including `person`, `hardhat`, `no-hardhat`, `safety vest` and `no-safety vest` | MIT declared; exact-weight scope, publisher authority and upstream/data obligations remain unresolved | A five-class, MIT-declared lead if the rights reviewer can accept digest-bound permission and lineage; operational verification is still required |
| `Hansung-Cho/yolov8-ppe-detection`, pinned `best.pt` | Person and equivalent positive/negative helmet and vest labels | MIT declared; exact-weight rights and upstream obligations unresolved; training-data lineage incomplete | Another five-class, MIT-declared lead, subject to rights acceptance and operational verification; publisher card/notebook metric differences still need explanation |
| `ayushgupta7777/safetyvision-yolov8`, pinned `v2/best.pt` | Person and equivalent positive/negative helmet and vest labels | Publisher explicitly declares AGPL-3.0 model weights | Five-class technical coverage, but the declared license does not meet the attachment's permissive-license condition; consideration would require a valid alternative permissive grant or explicit owner-authorized requirement change and rights review |
| `snehilsanyal/Construction-Site-Safety-PPE-Detection`, pinned `models/best.pt` | Person and equivalent positive/negative helmet and vest labels | No verified weight-license grant | Five-class technical lead only if the rightsholder supplies acceptable permissive weight rights and upstream/data lineage; current raw-GitHub source is also unsupported by the application downloader |
| `hafizqaim/Workspace-Safety-Detection-using-YOLOv8`, `v1.0.0/best.pt` | Person, helmet, negative helmet and positive vest; no explicit negative vest in the inspected metadata | No accepted weight grant | Does not cover all five classes in the inspected taxonomy; licensing clarification or renaming cannot create negative vest |
| `keremberke/yolov8m-protective-equipment-detection` | Published taxonomy lacks Person and both vest classes; no supplied checkpoint verification | No accepted weight grant; dataset CC BY 4.0 is separate | Not a complete fallback on present evidence; taxonomy mapping alone cannot close those gaps |

The pinned revisions, sizes and fingerprints for the four alternatives are recorded in the research and inspection utility. Baskarmother, Hansung and SafetyVision are checked against recorded size/SHA-256; Snehil's published identity check uses size and Git blob SHA-1, not an independently published SHA-256 reference. The supplied findings are incorporated as prior inspection results, not independently reproduced measurements here. No persisted raw inspection report was supplied.

The utility parses literal serialized names and class-count metadata as inert ZIP/pickle opcodes; it never reconstructs or executes model objects. Thus static label presence is stronger than a model-card claim, but does not validate tensors/output heads, certify architecture or safe loading, or demonstrate detections. Conditional label normalization may reconcile Hardhat with `helmet` and explicit NO-Hardhat with `no_helmet`; it cannot manufacture missing classes. Absence of a positive PPE detection must not become a negative detection.

### Licensing review and conditional priority

The authoritative attachment says **permissive licenses**. Earlier references below to a broadly “acceptable” license must not be read as permission to accept AGPL under that unchanged condition. MIT is permissive as a license family, but a Hub declaration alone does not establish an accepted grant covering the exact checkpoint and all applicable upstream material. Dataset-CC declarations likewise do not license weights; the particular dataset license and contributing-source rights require separate review.

The recorded Baskarmother review identifies unresolved initialization identity, publisher authority, training-software terms and contributing-data rights. Ultralytics' runtime AGPL terms and its broader vendor position on trained models must be assessed separately, without declaring that every private application or detection output is automatically AGPL-covered. A hypothetical Enterprise agreement neither proves rights to a third-party checkpoint nor automatically satisfies the permissive-weight sourcing requirement.

If prioritizing evidence collection rather than adoption, Baskarmother and Hansung are the closest declared-license leads because both combine static five-label coverage with MIT metadata. Baskarmother has more explicit linked dataset declarations in the recorded review; Hansung has publisher-saved validation evidence, but its dataset lineage and conflicting metrics remain unresolved. Those documentary differences do not establish an accuracy or speed winner. Snehil depends on obtaining a weight grant; SafetyVision v2 is not a permissive-license option on its currently declared terms. No candidate is selected or approved.

### What remains for full FR-1 and FR-2 readiness

For FR-1, later separately authorized verification must establish usable direct Person boxes and explicit positive/negative PPE outputs, compatibility with the pinned Ultralytics 8.3.70/Torch 2.6.0 environment, and measured real-time frame ingestion/inference on agreed hardware and settings. Person label presence is not proof of observed Person detections or reliable bottom-center localization. The application must still provide consistent normalized classes, confidences and bounding boxes; complete labels do not implement ingestion, adapters or person-level PPE handling.

For FR-2, Person-capable candidates avoid a known taxonomy need for a second detector, but none provides the restricted-zone feature merely by containing Person. The backend must use the clip-specific polygon in static JSON/YAML, calculate the Person box bottom center `((x1 + x2) / 2, y_max)`, and apply ray-casting point-in-polygon in the same coordinate system. Coordinate scaling, boundary behavior and incursion correctness still require implementation and verification after the real-model FR-1 gate. No geometry implementation, secondary detector, heuristic Person region or FR-2 scope reduction is authorized here.

The required public 100-clip dataset remains unidentified. Dataset/version, annotations, rights, evaluation procedure, persisted results and whether displayed mAP50 covers individual classes, a specified mean or both remain unresolved. Publisher image-dataset scores cannot substitute for this evaluation or rank candidates on Renewi footage. No candidate has verified local throughput, operational five-class detections or a completed authoritative 100-clip evaluation.

Basic authentication and an IP allow-list are application/deployment controls, not model capabilities. Credential provisioning, allow-list configuration and backend/frontend protection scope remain to be specified and verified. Forklift detection remains outside this PEOPLE/PPE scope; generic COCO availability does not establish a forklift class.

The conditional conclusion is therefore: retain Baskarmother and Hansung as rights-review and operational-verification leads, retain Snehil as a rights-unresolved lead, and distinguish SafetyVision's complete labels from its nonpermissive declared license. Approve none on current evidence. The preferred-model configuration and all false approval/capability flags remain unchanged; the guarded downloader still rejects incomplete review. This comparison changes documentation only and does not authorize implementation or relax the requirements.

## Preferred candidate

| Field | Inspected evidence |
| --- | --- |
| Repository | [hafizqaim/Workspace-Safety-Detection-using-YOLOv8](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8) |
| Inspected repository commit | `8f16e157b0533e5ef62bb48ca829b612bad63d3b` |
| Release | `v1.0.0`; release ID `232751089`; GitHub reports `immutable: false` |
| Release tag commit | `da9e8a3f41b55e7cc3d6ce400528b0dba939ec33` |
| Architecture | YOLOv8n according to the release body and training notebook; checkpoint not loaded |
| Weights | `best.pt`, asset ID `273300310`, 6,249,635 bytes |
| Published digest | `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836` (GitHub API SHA-256; **not a locally verified hash**) |
| Browser source | [release download](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/download/v1.0.0/best.pt) |
| Downloader source | [asset API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/assets/273300310) |
| License | **Unknown/unapproved**. GitHub API returns `license: null`; inspected recursive tree contains no license file |
| Training dataset | Notebook references Roboflow “PPE Detection v3” through a Kaggle dataset; usage rights not verified |
| Download/load status | Not downloaded or deserialized; license gate prevents execution |

Sources: [repository API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8),
[release API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/232751089),
[tag API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/ref/tags/v1.0.0),
[pinned repository tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/8f16e157b0533e5ef62bb48ca829b612bad63d3b?recursive=1),
[pinned training notebook](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/workplace-safety.ipynb).

### Training taxonomy, not checkpoint verification

The notebook's ordered `names` list declares these zero-based IDs.
They have not been checked against the release checkpoint.

| ID | Raw name | Potential internal class |
| --- | --- | --- |
| 0 | Barefoots | out of scope |
| 1 | Ear-protection | out of scope |
| 2 | Harness | out of scope |
| 3 | No_Ear-Protection | out of scope |
| 4 | No_Glasses | out of scope |
| 5 | Sandals | out of scope |
| 6 | boots | out of scope |
| 7 | face_mask | out of scope |
| 8 | face_nomask | out of scope |
| 9 | glasses | out of scope |
| 10 | hand_glove | out of scope |
| 11 | hand_noglove | out of scope |
| 12 | head_helmet | helmet |
| 13 | head_nohelmet | no_helmet |
| 14 | person | person |
| 15 | shoes | out of scope |
| 16 | vest | safety_vest |

Person, helmet, negative helmet, and positive vest are declared. **No negative
vest class is declared.** Do not invent `NO-Safety Vest` or map absence of `vest`
to `no_safety_vest`. This candidate does not satisfy the planned five-class
verification contract based on its published training taxonomy.

The Hugging Face model URL using the preferred repository name returned 404.
The GitHub README links a separate [demo Space](https://huggingface.co/spaces/hafizqaim/Workspace-Safety-Detection),
revision `c170c60a29a4eafed23055469e1ee15fad930243`; its API metadata also has no
license declaration. Hosting that copy does not resolve usage rights.

## Named fallback

| Field | Inspected evidence |
| --- | --- |
| Repository | [keremberke/yolov8m-protective-equipment-detection](https://huggingface.co/keremberke/yolov8m-protective-equipment-detection) |
| Revision | `8731f35c09d868473e085341c66dbb2e31559e0b` |
| Architecture | YOLOv8m according to model name/card; config declares `model_type: v8` |
| Weights source | [pinned best.pt URL](https://huggingface.co/keremberke/yolov8m-protective-equipment-detection/resolve/8731f35c09d868473e085341c66dbb2e31559e0b/best.pt) |
| Published weight metadata | 51,998,624 bytes; Hub LFS SHA-256 `ddc564fc57d9e8be0eb5bd1eec83cbd9d8aaca66b843ef0ccfdb4a4240c655a1`; **not locally verified**, not downloaded |
| License | No explicit license in inspected card/API metadata; API sibling list contains no LICENSE file |
| Runtime compatibility | Card recommends Ultralytics 8.0.23 and ultralyticsplus 0.0.24; compatibility with this environment not tested |
| Dataset | `keremberke/protective-equipment-detection`; pinned card, export notice, and loader declare CC BY 4.0 for the dataset, not the model weights; rights review remains pending |
| Selection | Not approved; no silent switch |

The [pinned card](https://huggingface.co/keremberke/yolov8m-protective-equipment-detection/blob/8731f35c09d868473e085341c66dbb2e31559e0b/README.md)
lists `glove`, `goggles`, `helmet`, `mask`, `no_glove`, `no_goggles`,
`no_helmet`, `no_mask`, `no_shoes`, `shoes`. The card order is **not verified
checkpoint class IDs**. The [pinned config](https://huggingface.co/keremberke/yolov8m-protective-equipment-detection/blob/8731f35c09d868473e085341c66dbb2e31559e0b/config.json)
contains no class map. Person, positive vest, and negative vest are not listed.
This fallback cannot fulfill the five-class requirement or supply FR-2 person
boxes. No secondary detector or heuristic is implemented.

## STEP-01 continuation investigation — 2026-10-03

Primary-source requests succeeded for the evidence below. No model binaries,
dataset archives, or remote code were executed; no model binaries or dataset
archives were downloaded. Remote Python source was inspected as text only. Search
results for similarly named Kaggle datasets are not provenance evidence and
were not used to assign a license or substitute a model.

| Evidence | Finding | Gate consequence |
| --- | --- | --- |
| [Preferred release-tag tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/da9e8a3f41b55e7cc3d6ce400528b0dba939ec33?recursive=1) and [tag README](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/da9e8a3f41b55e7cc3d6ce400528b0dba939ec33/README.md) | Non-truncated tree contains only `.gitignore`, `README.md`, and `inference.py`; no license or training notebook. README provides no explicit license grant. | The tag does not bind the later notebook taxonomy to the release bytes. Weights rights and actual classes remain unknown. |
| [Preferred commit history](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/commits?per_page=100) and pinned notebook cited above | Notebook was added at `e8b7834d68a14e5e806a29a1b3111b67c443d39d`, after the tag commit in history. It trains `yolov8n.pt` with 17 names and references `/kaggle/input/ppe-objection-detection/datasets/ppe detection.v3i.yolov8/`. | Architecture/training taxonomy have source evidence, not checkpoint verification. Exact Kaggle owner/version and original Roboflow source/rights are still unidentified. No negative vest is declared. |
| [Preferred pinned inference script](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/inference.py) | Demo filters predictions to `classes=[12, 16]`, described as helmet and vest. | Demo behavior is not evidence of Person or negative-class outputs, nor a substitute for inspecting checkpoint names. |
| [Pinned demo Space tree](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection/tree/c170c60a29a4eafed23055469e1ee15fad930243?recursive=true) and [card](https://huggingface.co/spaces/hafizqaim/Workspace-Safety-Detection/blob/c170c60a29a4eafed23055469e1ee15fad930243/README.md) | `best.pt` LFS digest and size match the GitHub release's published metadata; no license declaration/file. Notebook blob `671498f3bda191d334fa567e25fd31017d84b7f0` matches the inspected GitHub notebook. | Corroborates published asset identity only. A mirror does not grant rights or verify local bytes/classes. |
| [Existing preferred issue #1](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1) and [comments API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1/comments) | Existing issue asks for exact `v1.0.0/best.pt` rights, upstream/data obligations, and ordered class map. Open, zero comments at inspection. No issue was created or posted in this investigation. | A requester’s question is not maintainer permission. There is no reply resolving either gate. |
| [Fallback model API with blobs](https://huggingface.co/api/models/keremberke/yolov8m-protective-equipment-detection?blobs=true) and [discussions API](https://huggingface.co/api/models/keremberke/yolov8m-protective-equipment-detection/discussions) | Revision still `8731f35c09d868473e085341c66dbb2e31559e0b`; published LFS size/digest recorded above. No license declaration/file; discussion count zero. | Added integrity metadata does not establish weights permission or missing capabilities. |
| [Fallback pinned dataset card](https://huggingface.co/datasets/keremberke/protective-equipment-detection/blob/90d2c6da950a6168fcee20ec69e194a034f44eef/README.md), [export notice](https://huggingface.co/datasets/keremberke/protective-equipment-detection/blob/90d2c6da950a6168fcee20ec69e194a034f44eef/README.dataset.txt), and [loader](https://huggingface.co/datasets/keremberke/protective-equipment-detection/blob/90d2c6da950a6168fcee20ec69e194a034f44eef/protective-equipment-detection.py) | Card and loader declare CC BY 4.0; loader `_CATEGORIES` matches the model card's ten labels. Card links Roboflow `personal-protective-equipment/ppes-kaxsi`, version 7. Older export notice also mentions `suit`/`no-suit`, with provider shown as `undefined`. | Dataset declarations are now evidenced, but do not license the trained checkpoint. Legacy suit labels must not become vest aliases: they are absent from the loader/model card and their semantics are unverified. Person is still absent. |

**Decision unchanged:** neither named candidate can be approved on this
evidence. The preferred published training taxonomy covers four of the five
required canonical classes; the fallback published model taxonomy covers only
`helmet` and `no_helmet`. Actual checkpoint IDs/names remain unverified for
both. No absence-based negative PPE inference, secondary Person detector,
class remapping invention, model substitution, or scope relaxation is approved.

Focused validation: existing downloader regression suite ran with
`.venv/bin/python -m pytest backend/tests/test_download_model.py -q -p no:cacheprovider`:
**25 passed in 0.30 s**. This validates the existing tooling, not real-model
capability, rights approval, or complete VAL-01. Earlier environment checks
remain historical; no new environment rebuild, image/video inference, or
100-clip evaluation was performed.

## Final bounded provenance check — 2026-10-03

Seven read-only primary-source API requests succeeded after a shell syntax
retry. The retry did not fetch or execute any model asset. Only outstanding
maintainer responses and changed metadata were checked; completed environment,
downloader, dataset, and historical taxonomy checks were not repeated.

| Authoritative source | Observed result | Approval consequence |
| --- | --- | --- |
| [Preferred repository metadata](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8) and [latest commit](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/commits?per_page=1) | License remains null; head remains `8f16e157b0533e5ef62bb48ca829b612bad63d3b`. | No new repository rights or revised source evidence. |
| [Preferred issue #1](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1) and [comments](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1/comments?per_page=100) | Open, zero comments; comments response is empty. The issue requests exact-asset rights, upstream/data obligations, and ordered checkpoint classes. | No maintainer answer, permission, or class map. The question itself is not evidence of a grant. |
| [Preferred Space metadata](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection) | Revision remains `c170c60a29a4eafed23055469e1ee15fad930243`; no card license or listed license file. | No new mirror rights evidence. |
| [Fallback model metadata](https://huggingface.co/api/models/keremberke/yolov8m-protective-equipment-detection) and [discussions](https://huggingface.co/api/models/keremberke/yolov8m-protective-equipment-detection/discussions) | Revision remains `8731f35c09d868473e085341c66dbb2e31559e0b`; no card license or listed license file; zero discussions. | No weight-specific rights or new class evidence. |

**Final outcome:** OPEN-01 is unresolved; STEP-01 remains failed and execution
blocked. No model/configuration change, substitution, requirements relaxation,
weight download/deserialization, inference, or evaluation occurred. This is
provenance evidence only, not a new test pass or complete VAL-01.

**Owner-dependent blocker:** The PoC/model owner must provide a rightsholder
statement covering the exact asset/digest and intended use, including upstream
initialization/data obligations, plus a complete ordered class map tied to that
same checkpoint and evidence of all five required canonical classes. The rights
reviewer must explicitly accept the rights. Current published taxonomies lack
required classes, so obtaining a license alone will not unblock the contract.
Do not repeat identical public-source checks without new owner evidence or a
changed authoritative source. Do not enable approval on unanswered requests,
dataset licensing, or notebook declarations.

## Alternative-model investigation (authorization not recorded) — 2026-10-03

A prior session reports an investigation of alternatives; no authorization is
recorded in this repository. It covered investigation only, not selection, substitution,
checkpoint loading, or implementation. The unchanged requirements still require
YOLOv8, accepted exact-weight licensing, direct Person detections, and explicit
positive/negative helmet and vest classes.

The alternative-model research
records five primary-source investigations, pinned revisions, published artifact
sizes/digests, conditional class mappings, and unresolved rights/capability
evidence. Baskarmother and Hansung Cho declare MIT and all five labels; Hansung's
card examples are corroborated by linked training YAML. Neither declaration
establishes accepted upstream/exact-weight rights or verified checkpoint classes.
SafetyVision explicitly declares AGPL-3.0 model weights and all five labels, but
license acceptability and actual artifact capability remain unverified. Snehil
Sanyal's training taxonomy covers all five labels but its repository has no
identified license grant. Qualcomm's documented custom two-class architecture
does not meet the unchanged YOLOv8 five-class contract.

**Outcome unchanged:** no model approved. Only public metadata and text were
retrieved; no weights or dataset archives were downloaded, no checkpoint was
loaded, and no inference, tests, or evaluation were run in this investigation.
Published LFS digests are not local integrity checks; training/card taxonomies
are not verified checkpoint contents. `config/model.yaml` and plan execution
status are unchanged. The research identifies new targeted evidence requests,
not permission to bypass OPEN-01 or repeat the exhausted original-candidate
checks.

## Targeted Baskarmother evidence — 2026-10-03

The focused follow-up in the alternative-model research
rechecked Baskarmother's pinned model card, revision-specific artifact metadata,
commit history, and discussions. Revision
`3213ed51de90cbc76e577e6944e84f7c74343526` still identifies `best.pt` as
6,258,474 bytes with published LFS SHA-256
`8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`.
This is public artifact identity, not a locally verified hash or an accepted
weight license. MIT remains a card declaration; the inspected files contain no
weight-specific rights explanation or upstream reconciliation, and the Hub
reports zero discussions. Ultralytics' stated AGPL/Enterprise position still
requires rights review; no definitive license conclusion is inferred.

The model card declares `person` at ID 9, `hardhat` at 4, `no-hardhat` at 6,
`safety vest` at 12, and `no-safety vest` at 8. Pinned dataset revision
`a19eace121442bce60da9f5036dc16bf9f2f6fa6` corroborates the same ordered
labels in its card and loader text. This verifies documentary five-class
coverage, not the names/head contents or observed detections of this checkpoint.
The dataset card/loader/notice declare CC BY 4.0; export notices identify
Roboflow version 1 and contributing video/image sources. Exact training use and
contributor rights remain unverified; dataset declarations do not grant weights
rights or satisfy the 100-clip evaluation requirement.

The publisher must supply digest-bound weight permission and upstream/data
lineage, plus a complete trustworthy class/architecture report for the same
artifact. The PoC/model owner and rights reviewer must assess that evidence for
the intended use. Later real-model verification and any safe inspection require
separate authorization; matching a digest does not make deserialization safe.
**No approval or substitution:** the configured preferred model and all false
approval/capability flags remain unchanged. Only public metadata and text were
retrieved; no checkpoint or dataset archive was downloaded, no model was loaded,
and no inference, tests, or evaluation were run. Implementation remains paused.

## Targeted Hansung Cho evidence — 2026-10-03

The targeted research
rechecked pinned Hub metadata/card, upload history, discussions, the linked
GitHub tree, training YAML, notebook JSON/text, and demo sources. Revision
`ac0027bd38bc619d5ce4f52b4cc01beb87d8b958` identifies `best.pt` as
6,250,090 bytes with published LFS SHA-256
`2419700bbe3b8d38f9000655d9cf952a4bc93ef6c143baf8b49a0abde5d0760f`.
This is remote artifact metadata, not a locally verified hash or safe checkpoint.
MIT remains a Hub card declaration without an exact-weight rights explanation
or upstream reconciliation. The linked GitHub repository reports license null
and has no license file in its inspected tree; Hub discussions and the GitHub
all-state issue query are empty. No permission request was sent.

Pinned YAML declares `Person` at ID 5, `Hardhat` at 0, `NO-Hardhat` at 2,
`Safety Vest` at 7, and `NO-Safety Vest` at 4. The notebook's saved validation
text reports all five classes for a local `ppe_train/weights/best.pt` run and
its sample prediction reports Persons, Hardhats, and Safety Vests. This is
stronger documentary evidence than card examples alone, but no hash or
attestation binds that local run, its architecture, or its class map to the
Hub artifact. Direct Person boxes and explicit negative helmet/vest outputs
from the exact checkpoint remain unverified here. Card example spelling
uses `No-` while YAML uses `NO-`; neither becomes a configured alias.

The notebook reports a 114-image validation with overall mAP50 0.750,
whereas the Hub card reports 0.744 and different precision/recall values.
Neither is a reproduced Renewi metric or the required 100-clip evaluation,
and the publisher has not explained which run corresponds to the Hub digest.
The notebook uses a local dataset path without a provider/version/license
record and names `yolov8n.pt` without an immutable initialization identity.
Saved validation uses Ultralytics 8.3.232 and Torch 2.9.0+cu126, versus the
project's 8.3.70 and 2.6.0; the publisher's demo pins yet another stack.
Compatibility remains untested, not proven incompatible.

Accepted exact-weight permission and upstream/data lineage require the
publisher/rightsholder, PoC/model owner, and rights reviewer. A trustworthy
complete ordered taxonomy/architecture report must identify the same digest,
link the uploaded checkpoint to the reported run, and explain the metrics
discrepancy. Later safe inspection and real-model five-class verification
require separate authorization; digest agreement does not make loading safe.
**Decision unchanged:** no approval or substitution. The configured model and
false approval/capability flags are untouched. Only public metadata/text was
retrieved, the notebook was not executed, no weights or dataset archives were
downloaded, and no inference, tests, or evaluation were run. Implementation
remains paused.

## How to assess suitability for PEOPLE/PPE worker safety

This guidance applies the authoritative requirements to the existing candidate findings. It is a selection checklist, not an implementation plan, model approval, or authorization to obtain or load weights. The intended PoC must support FR-1 person/PPE detection and compliance, FR-2 restricted-zone incursion, and reproducible metrics/provenance. A generic construction-safety label or a high published aggregate score is not sufficient.

Separate documentary eligibility, operational suitability, and adoption. Documentary eligibility asks whether accepted rights and trustworthy architecture/taxonomy evidence cover the exact artifact. Operational suitability requires later separately authorized verification and evaluation. Adoption requires an explicit documented owner decision and any necessary plan reapproval. Passing one stage does not imply the others have passed. Implementation remains blocked at STEP-01; FR-2 must still wait for real-model FR-1 verification.

### Requirements-grounded selection checklist

For each candidate, record the evidence reference, artifact revision/digest, status, and unresolved owner question against every row. Use statuses such as declared, corroborated documentary evidence, verified for exact artifact, accepted by reviewer, or unresolved. Do not convert an unresolved item into a pass or award it a neutral score that hides a hard-gate failure.

| Examine | What satisfactory evidence must establish | Current assessment or limitation |
| --- | --- | --- |
| Public open weights and architecture | A specific public source asset, immutable repository revision, expected size/SHA-256, and trustworthy evidence that the exact artifact is YOLOv8. | Both alternatives declare YOLOv8n and have published identity metadata; neither has checkpoint-derived architecture verification here. |
| Acceptable exact-weight rights | A grant whose scope and authority cover the identified weights and intended use, with upstream initialization/software and training-data obligations understood and explicitly accepted by the rights reviewer. | Both cards declare MIT, but neither has accepted exact-weight rights or reconciled upstream obligations. Public hosting is not permission. |
| Complete taxonomy and configurable mapping | Complete ordered IDs/raw names and semantics for the same artifact, covering `person`, `helmet`, `no_helmet`, `safety_vest`, and `no_safety_vest`. Aliases must reflect actual verified names rather than card spelling guesses. | Both have documentary five-class coverage; neither has verified exact-checkpoint names/head contents. Published mappings remain conditional, not runtime aliases. |
| Direct Person boxes for FR-1 and FR-2 | Actual person bounding boxes, confidence and frame association, suitable for PPE association and the FR-2 bottom-center calculation `((x1 + x2) / 2, y2)`. | Person labels alone do not demonstrate boxes or usable ground-contact localization. Do not invent boxes or add a secondary detector/heuristic to bypass the unchanged contract. |
| Explicit positive and negative PPE signals | Separate helmet, negative-helmet, vest and negative-vest outputs with understood annotation semantics and boxes that can be associated with people. | Lack of a positive detection is not evidence of a negative class. Neither alternative has authorized Renewi verification of all four signals. |
| Compliance behavior and ambiguity | Evidence supporting all five required states: COMPLIANT, HELMET_MISSING, VEST_MISSING, HELMET_AND_VEST_MISSING and UNKNOWN. Incomplete, ambiguous or conflicting evidence must not silently become a violation or a compliance claim. | Detection accuracy alone does not establish correct person-level compliance. The compliance engine and association logic are not implemented. |
| Spatial association and zone suitability | PPE box geometry supports the required center-within-person association and deterministic overlap resolution; person boxes yield credible bottom centers near zone boundaries. | Crowded/overlapping people and truncated person boxes need particular scrutiny. A correct polygon algorithm cannot compensate for a missed person or inaccurate box. |
| Reproducible accuracy evidence | The model, dataset/version/source, weights identity, confidence/IoU settings, image size, date and project commit accompany overall mAP50, per-class AP50, precision and recall. | The authoritative annotated 100-clip dataset is still unidentified. No Renewi inference or evaluation has occurred. Publisher image benchmarks do not satisfy that requirement. |
| Local runtime and modular integration | Compatibility with the pinned project environment and normalized class/confidence/box/frame outputs through an adapter, without coupling compliance or geometry to raw YOLO objects. | The baseline is Python 3.11, Ultralytics 8.3.70 and Torch 2.6.0. Compatibility is untested; a publisher's different stack is a question to resolve, not proof of incompatibility. |
| Image/video throughput and configurability | Measured local throughput, latency and resource use under the selected image size, thresholds and frame sampling, sufficient for the agreed PoC needs while preserving real-time architectural support. | The attachment's 640 image size, 0.40 confidence, 0.45 IoU and 5 target FPS are conceptual examples, not demonstrated performance or fixed acceptance targets. |
| Scope and safe operation | No forklift logic, facial recognition or worker identity tracking; no need to execute untrusted remote code. Safe serialization review must be separate from integrity checking. Later API authentication/IP controls remain application responsibilities. | Extra labels confer no additional scope. Matching SHA-256 establishes bytes, not safe deserialization; a model card does not deliver authentication or an IP allow-list. |

The attachment specifies required capabilities and metric fields but does not set numeric minimum mAP50, per-class recall, latency, false-alarm or UNKNOWN-rate targets. The PoC/model owner and evaluation owner should define and record these acceptance targets before comparative evaluation, based on the consequences of missed hazards and false violations. These are additional decision criteria to agree, not requirements silently invented by this document. They cannot relax the five-class, rights or direct-Person contract.

### Comparing Baskarmother and Hansung Cho on the existing evidence

Use the saved alternative-model findings as evidence, not a leaderboard. Their different documentary strengths identify different follow-up questions. There is presently no common verified benchmark on which to choose the more accurate or faster model.

| Comparison dimension | Baskarmother | Hansung Cho | Meaning for selection |
| --- | --- | --- | --- |
| Declared architecture and artifact | YOLOv8n; revision `3213ed51de90cbc76e577e6944e84f7c74343526`; published `best.pt` identity recorded above. | YOLOv8n; revision `ac0027bd38bc619d5ce4f52b4cc01beb87d8b958`; published `best.pt` identity recorded above. | Both are plausible architectural leads, not verified runtime equivalents. Similar weight sizes do not establish speed, memory use or safety performance. |
| Required documentary mapping | Card IDs: 9/person, 4/hardhat, 6/no-hardhat, 12/safety vest, 8/no-safety vest; corroborated by the pinned dataset card/loader. | Training YAML IDs: 5/Person, 0/Hardhat, 2/NO-Hardhat, 7/Safety Vest, 4/NO-Safety Vest; saved validation reports all five labels. | Baskarmother has coherent card/dataset ordering; Hansung has additional saved validation evidence. Neither mapping is bound to the published checkpoint digest. |
| Rights and lineage | MIT card declaration; linked dataset declares CC BY 4.0, but exact training use, contributing source rights and upstream reconciliation remain unresolved. | MIT Hub declaration; linked GitHub has no identified license grant, and local dataset paths do not identify provider/version/license. Upstream reconciliation remains unresolved. | Neither passes accepted exact-weight rights. Dataset declarations cannot license weights or settle all source obligations. |
| Published performance evidence | Existing findings do not establish a reproduced, digest-bound benchmark suitable for Renewi comparison. | Local notebook reports overall mAP50 0.750 on 114 images; Hub card reports 0.744 with differing precision/recall. Neither report is bound to the Hub digest. | Missing comparable evidence does not mean zero accuracy. The Hansung discrepancy needs explanation, not selection of the larger number. |
| Class-specific safety signal | No exact-artifact operational evidence is established by the saved findings. | Saved local-run recall is 0.681 for Person, 0.522 for NO-Hardhat and 0.580 for NO-Safety Vest; these are publisher reports, not Renewi measurements or accepted targets. | Negative-class and Person recall deserve explicit scrutiny, but these values cannot establish the Hub artifact's performance or rank it against Baskarmother. |
| Compatibility and observed outputs | Declared 640-pixel training; no local compatibility or real-image/video verification. | Saved notebook and demo use stacks different from each other and the project; no local compatibility or real-image/video verification. | Neither has demonstrated usable Person/PPE outputs in the pinned Renewi runtime. |

For Baskarmother, examine a digest-bound complete class/architecture report, exact initialization and training-data lineage, and the authority and scope of the MIT claim. For Hansung Cho, examine the same rights and checkpoint evidence, plus the upload-to-training-run linkage, exact dataset identity, explanation of the card/notebook metric discrepancy and compatibility with the pinned environment. A trustworthy publisher report can improve documentary eligibility but cannot replace later authorized real-model verification.

### What a fair operational comparison would need to show

Only after separate rights/safety review and authorization, compare eligible artifacts on the same reviewed, licensed, annotated dataset and split with the same preprocessing, box-coordinate conventions and documented inference settings. The required authoritative 100-clip dataset must first be identified; convenient training images or a 114-image validation report cannot be relabelled as that evaluation. Check training/evaluation overlap to avoid measuring memorization. If tuning thresholds per candidate, use a separate validation split, record the tuning procedure, and keep the final comparison set held out. State whether the reported overall mean covers all model classes or the five required classes.

Report overall mAP50 and each required class's AP50, precision and recall together with class support counts. Examine missed persons and missed explicit negative PPE signals, not just positive helmet/vest scores. A strong average can hide weak negative-vest detection; different extra-class taxonomies also make unqualified overall means misleading. Distinguish detection metrics from person-level compliance and zone-event outcomes.

Examine representative reviewed fixtures across camera angles, lighting, worker distance, partial occlusion, PPE styles, crowded overlap and partial-body visibility. These are recommended robustness dimensions, not claimed dataset coverage. Inspect whether PPE is assigned to the correct person, whether conflicting/insufficient evidence remains UNKNOWN, and whether bottom-center errors or sampling miss incursions near polygon boundaries. The required compliant, helmet-missing, vest-missing, both-missing and unknown cases should remain distinguishable. Correct logic with fabricated detections is not evidence of real-model suitability.

For decision-making, compare false violations, missed explicit violations, UNKNOWN frequency, wrong-person association and zone-incursion errors alongside latency/throughput and memory measurements on the same local hardware. These are recommended supplementary measures, not metrics already produced or fixed contractual thresholds. Record image size, sampling, thresholds, runtime versions and hardware so any apparent advantage is reproducible. Do not infer a vest violation from an undetected vest to make recall appear better, or introduce identity tracking to improve results.

### Decision rule and present recommendation

Use hard gates first, comparative quality second. If rights, exact-artifact architecture/taxonomy or required direct Person/five-class evidence is unresolved, retain that candidate as an evidence lead rather than an adoptable model. Once an eligible candidate has separately authorized operational results, compare them against pre-agreed safety and runtime criteria. If only one qualifies, document why it qualifies; if both qualify, prefer the one with the better reproducible required-class and person-level safety performance within the agreed local resource budget, with maintainability and provenance as further considerations. If neither qualifies, select neither rather than silently changing the requirements.

On the existing evidence, **neither Baskarmother nor Hansung Cho can presently be recommended for adoption**, and there is no supported accuracy winner. Both warrant targeted evidence requests, not repeated identical public-source checks. The publisher/rightsholder supplies exact-artifact rights, lineage and class/architecture evidence; the PoC/model owner and rights reviewer assess acceptability; the evaluation owner identifies the dataset and agreed quality criteria; later authorized verification establishes operational suitability. This completed selection guidance does not change `approved`, `actual_classes_verified` or `required_classes_supported`, substitute a model, authorize weight download/loading, revise the plan, or resume implementation.

## Preferred hafizqaim requirement reassessment — 2026-10-03

This reassessment applies the authoritative attachment to the originally preferred `hafizqaim/Workspace-Safety-Detection-using-YOLOv8` candidate, not to a replacement. Primary-source checks began at **2026-10-03 07:25 UTC**. An initial shell parsing error occurred before network execution; the corrected read-only requests succeeded. The notebook was parsed as inert JSON and selected source cells were read, never executed. Only public metadata and text were retrieved. No weights, dataset archives, or remote applications were downloaded or run.

### Refreshed primary-source evidence

| Source | Current observation | What it establishes |
| --- | --- | --- |
| [Repository API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8), [commit history](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/commits?per_page=100), and [head tree](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/trees/8f16e157b0533e5ef62bb48ca829b612bad63d3b?recursive=1) | Public repository; head remains `8f16e157b0533e5ef62bb48ca829b612bad63d3b`; license is null; non-truncated tree has no license file. | Public provenance is supported, but no newly identified license grant or source revision resolves acceptance. |
| [Release API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/releases/232751089) and [tag reference](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/git/ref/tags/v1.0.0) | `v1.0.0` still references commit `da9e8a3f41b55e7cc3d6ce400528b0dba939ec33`. Asset `273300310`, `best.pt`, remains 6,249,635 bytes with published SHA-256 `5464f555f1b9831e6f1f9adcab11063f9a081d62e6650c2f2154bd4c01720836`; release remains mutable. | Source/version and expected artifact identity are documented, not locally verified bytes, safe serialization, or checkpoint contents. |
| [Pinned notebook](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/workplace-safety.ipynb) and commit history | Notebook still requests `yolov8n.pt` training and declares the same 17 names. It was committed at `e8b7834d68a14e5e806a29a1b3111b67c443d39d` at 06:58:15 UTC on 2025-07-16, after the release published at 06:49:08 UTC. | Four required labels have training-intent evidence; negative vest is absent. Chronology does not prove a different model, but there is no digest-bound linkage to the released checkpoint. |
| [Pinned inference script](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/inference.py) | Calls inference with `classes=[12, 16]`, described as helmet and vest. | This demo filters out Person and negative-helmet labels. It cannot demonstrate the required full FR-1/FR-2 outputs and is not evidence that the checkpoint lacks the filtered labels. |
| [Issue #1](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1) and [comments API](https://api.github.com/repos/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/issues/1/comments?per_page=100) | Issue remains open with zero comments; comments response is empty. | No maintainer rights statement, complete checkpoint class map, or upstream/data clarification has arrived. No inquiry was submitted here. |
| [Space metadata](https://huggingface.co/api/spaces/hafizqaim/Workspace-Safety-Detection) | Revision remains `c170c60a29a4eafed23055469e1ee15fad930243`; card has no license and sibling list has no license file. | The demo mirror still supplies no new rights evidence. Its reported runtime error is a hosting observation, not proof of model incompatibility. |
| [Preferred Hugging Face model API](https://huggingface.co/api/models/hafizqaim/Workspace-Safety-Detection-using-YOLOv8) | Current unauthenticated response is HTTP 401, `Invalid username or password.`, unlike the earlier recorded 404. | Public model metadata could not be retrieved at that namespace. This does not establish existence, deletion, privacy, or a valid model license. The historical 404 remains a historical observation. |
| [Pinned README](https://github.com/hafizqaim/Workspace-Safety-Detection-using-YOLOv8/blob/8f16e157b0533e5ef62bb48ca829b612bad63d3b/README.md) and release body | README reports overall mAP50 0.735, precision 0.720 and recall 0.715; helmet AP50 0.866 and vest AP50 0.935. Release reports mAP50 0.735 without a full evaluation manifest. | These are publisher-reported image-dataset results, not reproduced Renewi measurements or evidence of the required 100-clip evaluation. Scores do not resolve missing negative-vest coverage. |

### Requirement-by-requirement result

**Satisfied** means the stated documentary requirement is supported at the explicitly identified evidence level, not model approval. **Unmet** means the required documented condition or deliverable is currently missing; it does not assert a secretly inspected checkpoint failure. **Unverified** means plausible declarations exist or an operational property is relevant, but sufficient exact-artifact or runtime evidence is unavailable. Application responsibilities are separated from model properties so the candidate is not credited with an unimplemented backend.

| Requirement from the attachment | Status | Supported match, gap, or unresolved evidence |
| --- | --- | --- |
| Public repository and published weight source | Satisfied — public availability only | GitHub publicly lists `v1.0.0/best.pt` and its asset identity. Public availability does not establish lawful open-weight reuse; that remains subject to the rights gate below. |
| Open weights with explicitly verified, acceptable licensing | Unmet | No accepted exact-weight grant or reviewer decision is documented. License null is not itself proof of prohibition, but public hosting is not permission. Upstream initialization/software and data obligations remain unresolved. |
| YOLOv8 architecture | Unverified for exact checkpoint | Release declares YOLOv8n and notebook requests `yolov8n.pt`. No trustworthy architecture report binds those declarations to the release SHA-256; the checkpoint was not loaded. |
| Repository, version/commit, weights, source URL and expected identity documented | Satisfied — published provenance | Repository head, release/tag commit, asset ID, URL, size and published digest are recorded above and in configuration. The mutable release is not an immutable artifact guarantee; a future authorized download must verify bytes. |
| Complete ordered actual classes and configurable canonical mapping | Unmet as an acceptance deliverable | The notebook's ordered training names are documented, not a verified release class map. No runtime aliases or class configuration were created. Exact names, IDs and annotation semantics must be established before configuring mappings. |
| Direct `person` boxes for FR-1 association and FR-2 bottom center | Unverified | Notebook ID 14 declares `person`; no exact-release Person boxes were observed. The demo filters Person out. A label declaration cannot establish usable ground-contact geometry. |
| `helmet` detection | Unverified | Notebook ID 12 declares `head_helmet`; conditional interpretation is `helmet`. Publisher reports helmet metrics, but exact-release outputs are not verified. |
| Explicit `no_helmet` detection | Unverified | Notebook ID 13 declares `head_nohelmet`; conditional interpretation is `no_helmet`. The demo excludes that class and no exact-release negative output was verified. |
| `safety_vest` detection | Unverified | Notebook ID 16 declares `vest`; conditional interpretation is `safety_vest`. Publisher reports vest metrics, not verified Renewi outputs. |
| Explicit `no_safety_vest` detection | Unmet in published taxonomy; checkpoint unverified | None of the 17 declared labels is a negative-vest class. No new manifest or maintainer response establishes one in the release. Missing `vest` cannot be mapped to `no_safety_vest`. |
| All five required canonical classes in one accepted candidate | Unmet | Published training coverage is four of five; verified exact-checkpoint five-class evidence and accepted rights are absent. A license alone cannot fix this documentary capability gap. |
| Normalized class/confidence/box/frame outputs behind an adapter | Unmet — application deliverable | Existing local code provides guarded download tooling, not the inference adapter. Upstream plotting does not implement the required normalized contract. No implementation was resumed. |
| Image/video ingestion, configurable sampling and inference settings, local runtime suitability | Unverified operational suitability | Upstream source indicates OpenCV/video intent, but no Renewi image/video run, throughput measurement, or compatibility check against Ultralytics 8.3.70/Torch 2.6.0 occurred. Example thresholds/FPS in the attachment are not demonstrated acceptance targets. |
| PPE/person spatial association and deterministic overlap handling | Unmet — application deliverable | No Renewi association engine is implemented or verified. Filtered helmet/vest plotting does not provide the required person-level association. |
| Five compliance states, explicit negatives and UNKNOWN for ambiguity | Unmet — application deliverable and evidence gap | No Renewi compliance engine is implemented. Published absence of negative vest prevents documentary support for the full explicit-negative contract; absence-based violations are prohibited. |
| Configured polygons, bottom-center geometry and structured FR-2 events | Unmet — application deliverable; model prerequisite unverified | Person boxes remain unverified and local zone processing is not implemented. No secondary detector, invented boxes, heuristic, or FR-2 scope reduction is authorized. |
| Reproducible 100-clip evaluation and required metrics/provenance fields | Unmet | Authoritative annotated dataset remains unidentified and no evaluation was run. Published image benchmarks lack the required Renewi dataset/run provenance and cannot be presented as completed BRD evaluation. |
| Accuracy and local safety fitness | Unverified | No common accepted evaluation or real-model fixtures demonstrate required-class AP50/precision/recall, compliance correctness, zone correctness or resource suitability. The attachment sets no numeric minimum accuracy or latency threshold. |
| Basic authentication and IP allow-list | Unmet — application deliverables | These are backend controls, not capabilities supplied by a PPE checkpoint. No implementation or deployment security verification was performed. |
| Modular, testable, configurable implementation and required geometry/compliance tests | Unmet for the full deliverable | Existing provenance/downloader tooling is not the complete FR-1/FR-2 backend. Historical downloader tests do not verify model capability, association, compliance or zone behavior; no tests were rerun here. |
| No forklift, facial recognition or worker identity tracking; no scope expansion | Satisfied — investigation scope only | No such feature was introduced. Extra notebook labels do not authorize expanded application behavior; future implementation remains separately gated. |

### Conclusion and precise remaining evidence

The preferred candidate has supported public provenance, declared YOLOv8n architecture, and documentary Person/helmet/negative-helmet/vest labels. It **does not presently satisfy the unchanged acceptance contract**: acceptable licensing has not been explicitly verified and accepted, the published taxonomy lacks negative vest, and exact-checkpoint architecture/classes and real operational outputs remain unverified. This is an evidence-based non-acceptance assessment, not a claim that the uninspected binary definitively lacks every declared class.

The publisher/rightsholder must provide digest-bound weight permission, upstream initialization and data lineage, and a trustworthy complete architecture/class manifest explaining the relationship between the release and later notebook. That manifest must establish explicit negative vest as well as the other four required classes; if the artifact truly lacks it, clarification or licensing alone cannot make it compliant. The PoC/model owner and rights reviewer must assess and document the intended-use rights. Separately authorized safety review and later real-model verification would still be necessary to establish usable Person/PPE boxes and runtime behavior; the evaluation owner must identify the authoritative annotated dataset before the 100-clip gate can be met. No replacement or requirement relaxation is authorized by this assessment.

`config/model.yaml` remains unchanged with `approved`, `actual_classes_verified`, and `required_classes_supported` all false, and null reviewer/license fields. Inspection of `scripts/download_model.py` confirms incomplete review is rejected before network/file writes and that the downloader never deserializes checkpoints. No model was approved or substituted, no approval gate was invoked to fetch weights, no local hash was claimed, no checkpoint was loaded, no inference/tests/evaluation occurred, and no plan status or implementation was changed. STEP-01 remains unresolved and implementation remains paused.

## Reconciliation of the supplied BRD model preference

The supplied statement identifies hafizqaim as preferred because it is said to include Person and all required positive/negative PPE classes, and identifies keremberke via ultralyticsplus as a viable rapid-integration fallback requiring taxonomy mapping. The preference is a selection intent, not evidence that either named artifact meets the acceptance contract. The required capabilities remain unchanged: the four mandatory PPE targets are Helmet, Safety Vest, NO-Hardhat and NO-Safety Vest, with direct Person detections additionally required for FR-1 association and FR-2 zone incursion. The four-row PPE matrix does not remove Person from the five-class contract.

### Required targets versus recorded candidate coverage

This matrix reconciles the supplied vocabulary with the already recorded, revision-specific findings. It introduces no fresh upstream inspection or checkpoint verification. Hafizqaim entries are notebook training declarations at the recorded repository head, not release-checkpoint IDs. Keremberke entries are published card labels at the recorded revision, not verified checkpoint IDs. Conditional mappings require verified names, IDs and annotation semantics before any runtime configuration.

| Required target | Canonical internal class | Hafizqaim published training evidence | Keremberke published model-card evidence |
| --- | --- | --- | --- |
| Helmet | `helmet` | ID 12 / `head_helmet`; conditional name mapping | `helmet`; conditional name mapping, ID unverified |
| Safety Vest | `safety_vest` | ID 16 / `vest`; conditional name mapping | Not listed; no supported mapping |
| NO-Hardhat | `no_helmet` | ID 13 / `head_nohelmet`; conditional explicit-negative mapping | `no_helmet`; conditional explicit-negative mapping, ID unverified |
| NO-Safety Vest | `no_safety_vest` | Not declared among the 17 names; no supported mapping | Not listed; no supported mapping |
| Person, additional FR-1/FR-2 requirement | `person` | ID 14 / `person`; direct boxes unverified | Not listed; direct boxes unsupported by published taxonomy |

Hafizqaim therefore has documentary coverage of three of the four mandatory PPE targets and four of the five required canonical classes. The assertion that its published taxonomy includes NO-Safety Vest is not supported by the existing findings. Its notebook was added after the release and has no digest-bound linkage to the release artifact. The demo's helmet/vest filter neither demonstrates Person or negative-class outputs nor proves that filtered classes are absent from the binary. Exact-checkpoint class coverage and actual outputs remain unverified.

Keremberke has documentary coverage of two of the four PPE targets and two of the five canonical classes. Its published taxonomy lacks Person and both vest classes. The ultralyticsplus usage recommendation establishes an integration approach described by the publisher, not tested compatibility or missing detection capabilities. It remains a named fallback candidate for investigation, but calling it a viable fallback for the unchanged complete PoC is not supported by the recorded evidence. Neither model has demonstrated the full required output set in Renewi.

### What taxonomy mapping can and cannot resolve

Mapping can normalize semantically equivalent labels, such as `head_helmet` to `helmet`, `head_nohelmet` to `no_helmet`, or an actual Safety Vest label to `safety_vest`. It cannot add an output head, train a missing class, generate direct Person boxes, establish exact-checkpoint identity, or resolve licensing. Legacy dataset `suit`/`no-suit` references do not establish vest classes in keremberke's published model taxonomy and must not be used as invented aliases.

In particular, no detected `vest` does not mean detected `no_safety_vest`, and no detected helmet does not mean detected `no_helmet`. Non-detection may reflect occlusion, missed detections, thresholds or genuinely absent PPE; it does not identify which explanation applies. Insufficient or conflicting person-associated evidence must remain UNKNOWN rather than being converted into COMPLIANT or a violation. UNKNOWN is an ambiguity outcome, not a replacement class or a waiver of the mandatory negative-vest requirement. Taxonomy mapping alone cannot close either candidate's documented coverage gaps.

### Reconciled preference and unchanged decision

An evidence-consistent formulation is: “Hafizqaim remains the BRD-named preferred candidate for investigation because its published training taxonomy declares Person, helmet, explicit negative helmet and positive vest. Explicit negative vest is not declared, and the exact release classes and acceptable weight rights remain unresolved. Keremberke remains the BRD-named fallback candidate for investigation; its published taxonomy declares helmet and explicit negative helmet but does not establish Person or either vest class. Both require exact-artifact verification and rights review; label normalization cannot supply missing capabilities.”

No acceptable exact-weight license has been accepted for either named candidate. A licensing clarification alone cannot cure a genuinely missing class, and a class-name mapping cannot cure the rights gap. Any later acceptance assessment needs trustworthy complete architecture/class evidence tied to the exact artifact digest, accepted intended-use rights and upstream/data obligations, and separately authorized safe real-model verification of all five classes and usable Person boxes. If the actual artifact lacks a mandatory class, it cannot satisfy the unchanged contract through renaming.

This reconciliation approves neither model and authorizes no replacement, secondary detector, heuristic, FR-2 removal, requirement relaxation or implementation resumption. No new download, checkpoint load, inference, evaluation or test run occurred. `approved`, `actual_classes_verified` and `required_classes_supported` remain false; source code, configuration and plan execution status are unchanged.

## Baskarmother exact-weight licensing review

The detailed licensing review covers `baskarmother/yolov8-ppe-construction`, revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, 6,258,474 bytes, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. It separates established published terms, supplied static-inspection findings, unresolved lineage and intended-use questions. It is not legal advice, a definitive legal determination, or a model adoption decision.

The re-read pinned publisher card and revision-specific Hub metadata confirm `license: mit`, `Base Model: yolov8n`, the linked dataset and artifact identity. The inspected files supply no standalone LICENSE, complete MIT text/copyright notice, exact initialization identity or upstream reconciliation. Missing a LICENSE does not itself invalidate the declaration; exact-weight scope and publisher authority remain insufficiently established for acceptance. The canonical MIT terms permit broad reuse subject to retaining copyright and permission notices and disclaim warranties. Those terms describe the declared license; they do not independently establish a grant from the publisher or cure missing upstream authority.

The supplied prior-inspection findings report matching size/SHA-256 and literal serialized presence of `person`, `hardhat`, `no-hardhat`, `safety vest` and `no-safety vest`. The existing inspection utility reads bounded ZIP/pickle-opcode metadata without unpickling. This later evidence improves exact-artifact label evidence beyond the earlier public-text stage, but does not establish model-head validity, architecture certification, usable Person boxes, actual inference, safe deserialization or rights. It is attributed to the supplied findings, not independently reproduced here; no persisted raw inspection report was supplied. Earlier uninspected-byte/class statements describe their historical investigation stage.

The runtime dependency Ultralytics 8.3.70 has AGPL version 3 license text. Sections 4–6 address applicable notices and source conditions when conveying covered works; section 13 addresses modified versions supporting remote network interaction. Section 2 permits running the unmodified Program and covered works not conveyed, subject to the license remaining in force, and covers output only if its content constitutes a covered work. These conditional terms must not be simplified into automatic publication of every private project, trained model or detection output. Separately, Ultralytics' current guidance asserts AGPL/Enterprise obligations for trained/fine-tuned models and private/internal/R&D use, even training from scratch. That is the vendor's position, not an independent ruling on Baskarmother's checkpoint. Neither the MIT declaration nor the vendor FAQ conclusively resolves covered-work scope.

The base-model name does not identify a pretrained initialization asset, its immutable revision/digest, actual training-software version, or additional permission. A hypothetical Enterprise agreement does not establish an executed grant, transferable publisher rights or coverage of this third-party digest. Its entity, term, software/model coverage and onward rights would need confirmation, and it would not automatically resolve publisher or data obligations. No procurement is authorized.

The pinned linked dataset declares CC BY 4.0 and Roboflow Construction Site Safety version 1, with 398 images. Its notice lists two YouTube sources and seven cloned image collections; exact training use and contributing permissions remain unverified. CC BY 4.0 requires applicable attribution, retained supplied notices, source/license links and modification indications when sharing licensed material, and limits the grant to the licensor's authority. It does not generally license privacy/publicity or patent/trademark rights. Dataset declarations do not license the weights, and this review does not decide whether the checkpoint is adapted material. The image dataset is not the authoritative required 100-clip evaluation dataset.

For local evaluation, API/demo access, delivery of code/containers/weights, or sharing source imagery, the rights reviewer must assess actual use rather than assume a “PoC” exemption. The publisher/rightsholder needs digest-bound grant scope, copyright holders/notices and authority, initialization source/version/digest, training software/version, any applicable additional permissions, and exact data lineage with contributing rights. The PoC/model owner must specify legal entities, users, network access, recipients and disclosure intentions. The designated reviewer must record acceptability and any necessary upstream clarification. Authentication/IP allow-listing is not a licensing exemption.

Primary sources and section-level analysis are linked in the detailed review: the pinned Baskarmother card/API, canonical MIT text, version-tagged Ultralytics LICENSE, vendor licensing guidance and published Enterprise terms, pinned dataset/export/source notices, and CC BY 4.0 legal code. **Outcome unchanged:** accepted exact-weight rights remain unresolved. The configured preferred model and false `approved`, `actual_classes_verified` and `required_classes_supported` flags are untouched. No model approval/substitution, source-code/configuration change, plan-status change, upstream inquiry, contract acceptance, purchase or implementation resumption occurred. This review retrieved public text/JSON only; no weights/datasets were obtained, no static inspection was rerun, no checkpoint was deserialized, and no inference, evaluation or tests were performed.

## Verifying Baskarmother against FR-1 and FR-2

This section applies the authoritative project requirements specifically to Baskarmother. It explains acceptance evidence, not implementation steps, permission to execute the model, or approval for adoption. The attachment requires public open weights, explicitly verified permissive/acceptable licensing, YOLOv8, five canonical classes, direct Person boxes, person-level PPE compliance and configured restricted-zone detection. Baskarmother is an alternative evidence lead, not the attachment's named preferred model. Its documentary review priority does not establish better accuracy or runtime performance.

### Completed checks and their evidence limits

The artifact under discussion is `baskarmother/yolov8-ppe-construction`, revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, 6,258,474 bytes, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. Existing records identify the public source, pinned card and expected artifact identity. The supplied prior static inspection reports matching size/SHA-256 and literal serialized presence of all five required labels. This invocation has not reproduced that inspection; no persisted raw inspection report was supplied. The inspection utility documents the fingerprint and inert-opcode method, not a saved successful run.

| Check already supported | Evidence level | What it does not establish |
| --- | --- | --- |
| Public repository, pinned source and artifact identity | Recorded primary-source metadata; supplied prior fingerprint match | Accepted reuse rights, safe loading or model execution |
| Person and all four positive/negative PPE labels | Supplied fingerprint-verified serialized-label finding | Valid output heads, trustworthy architecture verification or usable detections |
| Ordered class declarations | Pinned model card, corroborated by linked dataset card/loader | Independently reproduced checkpoint IDs, annotation semantics or configured runtime mapping |
| MIT declaration | Pinned publisher card metadata | Accepted exact-weight scope, publisher authority or reconciled upstream obligations |
| Linked dataset/version and CC BY 4.0 declarations | Pinned dataset documentation | Actual training lineage, all contributing permissions or the required 100-clip evaluation |

The conditional mapping is `person` → `person`, `hardhat` → `helmet`, `no-hardhat` → `no_helmet`, `safety vest` → `safety_vest`, and `no-safety vest` → `no_safety_vest`. The card declares IDs 9, 4, 6, 12 and 8 respectively. Those IDs remain attributed to the card rather than a raw checkpoint report reproduced here. Full ordered IDs/names, semantics and output-head agreement need trustworthy digest-bound evidence before operational mappings are accepted. Label normalization cannot manufacture detections or prove that a negative label means the required missing-PPE condition.

### Outstanding rights and loading-safety evidence

The publisher/rightsholder must establish a grant covering this exact digest and intended use, the applicable copyright holders/notices and authority, initialization source/revision/digest, training software/version and applicable upstream permissions. Exact training-data exports and contributing-source rights remain unresolved. The PoC/model owner must describe the intended users, legal entities, network access and recipients of copies; the designated rights reviewer must document acceptability for that use. A public MIT badge or dataset CC BY declaration alone cannot satisfy these outstanding checks.

The [existing licensing review](#baskarmother-exact-weight-licensing-review) separates weight rights, runtime AGPL terms, Ultralytics' broader vendor position and dataset obligations. Neither definitive AGPL inheritance nor unrestricted MIT eligibility is established for this artifact. A hypothetical Enterprise agreement is not evidence of an executed grant covering third-party weights. These are rights-review questions, not a legal determination in this guidance.

Separately, a matching digest identifies bytes; it does not make pickle-based loading safe. Architecture/head evidence, serialization safety review and explicit authorization remain necessary before any model load or inference. No approval flag should be toggled to perform a trial. The existing guarded downloader is acquisition tooling, not a safe-loader or acceptance evaluator.

### Practical FR-1 verification evidence

After separate rights/safety clearance and authorization, an acceptance record should identify the exact artifact digest, runtime versions, hardware, reviewed input fixtures, settings, expected observations and actual structured outputs. The project baseline is Python 3.11 with Ultralytics 8.3.70, Torch 2.6.0 and OpenCV 4.11.0.86; compatibility is not yet demonstrated. Record image and sampled-video behavior, resource release and failures, rather than treating a successful import or model initialization as FR-1 acceptance.

Real-image/video evidence must demonstrate actual direct Person boxes and each of the four PPE signals across reviewed fixtures, not necessarily all signals in one frame. Compare boxes and classes against annotations, including missing persons, explicit negative-PPE misses and false detections. Confirm normalized `class_name`, confidence, `[x1, y1, x2, y2]` coordinates and `frame_id` reach the application through an adapter. Check valid finite coordinates, box ordering and coordinate scaling back to the input frame. Unmapped extra labels must not expand the PEOPLE/PPE scope.

Application-level verification is distinct from checkpoint suitability. PPE centers must associate with the correct Person box using center-within-person geometry and a documented deterministic rule for overlapping people. Reviewed fixtures should expose crowded overlap, unassociated PPE, occlusion and contradictory or insufficient evidence. Verify the following outcomes without interpreting a missing positive detection as an explicit negative:

| Person-associated evidence | Required compliance outcome |
| --- | --- |
| Helmet and safety vest, without contradictory evidence | `COMPLIANT` |
| Explicit no-helmet and safety vest | `HELMET_MISSING` |
| Helmet and explicit no-safety-vest | `VEST_MISSING` |
| Explicit no-helmet and explicit no-safety-vest | `HELMET_AND_VEST_MISSING` |
| Insufficient, ambiguous or conflicting evidence | `UNKNOWN` |

Synthetic logic checks can establish mapping, box parsing, association and compliance rules, but cannot establish Baskarmother's detection capability. Conversely, correct detector outputs do not establish those application rules. Neither layer is implemented or operationally verified by this documentation update.

### Practical FR-2 verification evidence

FR-2 needs observed Person boxes from a real-model FR-1 verification, not merely the `person` label. For each box, the application must calculate `((x1 + x2) / 2, y2)` and apply ray-casting point-in-polygon against a clip-specific configured static polygon. Model input resizing or letterboxing must not leave boxes and polygons in different coordinate systems. The box centroid, PPE center and box/polygon overlap are not substitutes for the required bottom-center rule.

For example, the synthetic box `[100, 50, 200, 250]` has bottom center `(150, 250)`. Relative to the illustrative rectangle `[(120, 200), (180, 200), (180, 300), (120, 300)]`, that point is inside; the box centroid `(150, 150)` is outside. This is a geometry illustration, not a demo-zone definition, model result or executed test.

Verification evidence should cover inside/outside points, edges, corners and concave polygons if supported. The attachment requires boundary/corner tests but does not prescribe the inclusion policy: document one deterministic policy and compare outcomes against it rather than inventing a contractual answer. Confirm different clips use their own configured polygons and that inside detections produce structured events containing `event_type: ZONE_INCURSION`, `person_index`, `zone_id`, `frame_id` and `inside: true`.

Use annotated real clips to distinguish missed Person detections or inaccurate box bottoms from geometry errors. Sampling can miss a short incursion even when ray casting is correct; examine that effect under the chosen sampling settings. Do not invent Person regions, add identity tracking, substitute a secondary detector or drop FR-2 to bypass missing evidence. Correct synthetic geometry alone is not operational FR-2 acceptance.

### Evaluation and runtime evidence still required

The authoritative public annotated 100-clip dataset remains unidentified and no evaluation is complete. The evaluation owner must establish its name, version, source, clip manifest, annotations and rights, including whether the five required classes and representative scenarios are covered. Document train/evaluation overlap and any separate threshold-tuning split. The linked construction image dataset and publisher benchmarks are not substitutes for the required clip evaluation.

A reproducible evaluation record must include dataset identity, model name/revision, weights source/digest, confidence and IoU thresholds, image size, evaluation date and project Git commit, plus machine-readable overall mAP50, per-class AP50, precision and recall. State which classes the mean includes; extra model classes must not silently change the interpretation of a five-class comparison. State frame sampling and annotation/evaluation conventions for the clips. Supplement detection metrics with wrong-person association, false/missed compliance outcomes, UNKNOWN frequency and zone-incursion errors, clearly identifying these as recommended decision measures rather than results already obtained.

Local runtime measurements must identify hardware/device, software versions, resolution, thresholds and sampling settings. Distinguish cold loading/warm-up, steady inference latency and end-to-end frame-processing latency; report throughput and resource use under the intended image/video workload. The attachment's 640 image size, 0.40 confidence, 0.45 IoU and 5 target FPS are conceptual configuration examples, not fixed acceptance thresholds or demonstrated performance.

No numerical minimum accuracy, class recall, acceptable false-alarm/UNKNOWN rate or latency budget is established in the attachment. The PoC/model owner and evaluation owner should record appropriate acceptance criteria before interpreting future results. Without those criteria and measured results, a successful demonstration cannot support a quantitative suitability claim. Basic authentication and the IP allow-list are separate application controls, not capabilities delivered by these weights.

### Present determination and acceptance record

**Baskarmother has supported public provenance and supplied exact-artifact static five-label evidence; full FR-1 and FR-2 suitability remains unestablished.** Accepted licensing, trustworthy architecture/head and semantics evidence, safe authorized loading, operational Person/PPE detections, application behavior, local runtime measurements and the authoritative evaluation are outstanding.

For a future decision, record each requirement's evidence reference, artifact identity, expected result or agreed target, observed result, status, date and responsible reviewer. Keep statuses distinct: declared, supplied static finding, operationally verified, rights accepted and unresolved are not interchangeable. Licensing acceptance, real-model FR-1 verification, FR-2 application verification and the 100-clip evaluation each require their own evidence. None authorizes adoption by implication.

This guidance changes documentation only. The configured preferred candidate remains hafizqaim, and `approved`, `actual_classes_verified` and `required_classes_supported` remain false. Those configuration flags describe the configured candidate, not Baskarmother's separate static findings. No model asset was retrieved, no static inspection was rerun, no checkpoint was loaded, no inference/evaluation/test suite was run, and no source code, configuration, generated research page or implementation plan was changed. Implementation remains paused.

## Locally running and checking Baskarmother

These instructions answer how to check `baskarmother/yolov8-ppe-construction`; they are not authorization to download, deserialize or execute it. No command below was executed for this documentation update. Accepted exact-weight rights and loading safety remain unresolved, and implementation remains paused. Keep the configured candidate and all approval controls unchanged.

### Separate the three checks

Class inspection, prediction testing and application validation answer different questions. Supplied prior static inspection already reports the five required labels in the fingerprint-matched artifact. Runtime inspection would check what the installed loader exposes as `model.names`, but loading a checkpoint is itself a security-sensitive operation. Prediction testing would check whether reviewed images actually produce correct Person/PPE boxes. Application validation would check whether those boxes are correctly associated with people, converted into compliance states and used for restricted-zone events.

| Required canonical class | Expected Baskarmother ID | Expected literal name |
| --- | --- | --- |
| `person` | 9 | `person` |
| `helmet` | 4 | `hardhat` |
| `no_helmet` | 6 | `no-hardhat` |
| `safety_vest` | 12 | `safety vest` |
| `no_safety_vest` | 8 | `no-safety vest` |

These are the expected IDs/names from existing findings, not newly measured runtime results. Inspect the complete runtime map rather than filtering it to these five entries. A matching map establishes exposed taxonomy only: it does not prove valid output heads, annotation semantics, detection accuracy or safe loading.

### Prepare the documented local environment

Run the following from the nested application root, `Renewi_EHS_Lighthouse/`, not the outer workspace root. The repository baseline is Python 3.11, Ultralytics 8.3.70, Torch 2.6.0 and OpenCV 4.11.0.86. The lock records the tested macOS ARM64 resolution; other platforms need separate validation. Reuse the existing virtual environment when appropriate rather than relying on global packages.

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check --no-input -r backend/requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -m pytest backend/tests/test_download_model.py -q -p no:cacheprovider
```

These commands prepare dependencies and check synthetic downloader behavior. They do not load Baskarmother, establish class availability or grant weight rights. Installing Ultralytics also does not settle its licensing obligations. There is no implemented application inference service to start.

### Resolve acquisition and loading safety before runtime inspection

The artifact identity is revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, 6,258,474 bytes, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. Its pinned source is:

```text
https://huggingface.co/baskarmother/yolov8-ppe-construction/resolve/3213ed51de90cbc76e577e6944e84f7c74343526/best.pt
```

The existing `scripts/download_model.py` reads a reviewed configuration. The current `config/model.yaml` names hafizqaim, not Baskarmother, and intentionally fails its approval gate. It must not be edited to pretend that a Baskarmother trial is approved. Do not use direct acquisition as a workaround for that gate. Any later acquisition needs a separately authorized, documented process and a model-selection decision where applicable.

MIT is declared, but exact-weight grant scope, publisher authority, initialization and training-data lineage, and applicable upstream obligations remain unresolved. The PoC/model owner and designated rights reviewer must accept the intended use; a local PoC is not an automatic exemption. Separately, a security reviewer must assess checkpoint loading and authorize any runtime trial.

Use a disposable, least-privileged sandbox for an authorized load, without credentials, private worker footage or writable access to the application repository. Prefer disabling network access once reviewed dependencies, weights and fixtures are provisioned. Hash agreement identifies bytes, not safety. A virtual environment is dependency isolation, not a security sandbox. Do not work around loading failures with unrestricted `torch.load`, `weights_only=False`, blanket safe-global allow-listing, security-environment overrides, remote scripts or unreviewed package upgrades.

If a separately authorized static-only recheck is needed, the existing utility can be invoked from the application root as follows:

```sh
.venv/bin/python ../utils/inspect_ppe_candidates.py baskarmother
```

This utility downloads bounded bytes into memory and parses ZIP/pickle opcodes without reconstructing model objects. It does not retain a local checkpoint for inference or certify safe loading. Check both fingerprint booleans and the final report: it catches candidate exceptions and prints `status: unverified`, so process exit success alone is not a pass. Static metadata parsing is distinct from runtime class inspection and must not be used to bypass approval.

### Inspect runtime classes, then optionally predict reviewed images

The following example is documentation only, for a later rights-cleared and security-authorized sandbox. It assumes an existing reviewed local checkpoint; it does not download weights, modify configuration or implement an application adapter. Replace the weight-path placeholder with the sandbox's actual provisioned file.

For class inspection only, leave `PPE_IMAGES` unset. The code verifies artifact identity before importing the model loader, loads the checkpoint, prints every exposed class and requires the expected five ID/name pairs. Loading remains security-sensitive even when prediction is disabled.

```sh
export PPE_WEIGHTS="/absolute/path/to/reviewed/baskarmother-best.pt"
unset PPE_IMAGES
```

```sh
.venv/bin/python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

weights = Path(os.environ["PPE_WEIGHTS"]).resolve(strict=True)
expected_hash = "8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe"
if not weights.is_file() or weights.stat().st_size != 6258474:
    raise SystemExit("Checkpoint size/type mismatch; do not load")
if hashlib.sha256(weights.read_bytes()).hexdigest() != expected_hash:
    raise SystemExit("Checkpoint SHA-256 mismatch; do not load")

# Execute only after independent rights and loading-safety clearance.
from ultralytics import YOLO

model = YOLO(str(weights), task="detect")
raw_names = model.names
names = (
    {int(k): str(v) for k, v in raw_names.items()}
    if isinstance(raw_names, dict)
    else dict(enumerate(raw_names))
)
print(json.dumps({"runtime_names": names}, indent=2))
expected = {
    9: "person",
    4: "hardhat",
    6: "no-hardhat",
    12: "safety vest",
    8: "no-safety vest",
}
mismatches = {
    class_id: {"expected": name, "observed": names.get(class_id)}
    for class_id, name in expected.items()
    if names.get(class_id) != name
}
if mismatches:
    raise SystemExit("Unexpected runtime taxonomy: " + json.dumps(mismatches))
print("Expected five labels exposed; prediction capability is not yet proven.")

source = os.environ.get("PPE_IMAGES")
if source:
    images = Path(source).resolve(strict=True)
    if not images.is_dir():
        raise SystemExit("PPE_IMAGES must name a reviewed image directory")
    for result in model.predict(
        source=str(images), device="cpu", imgsz=640,
        conf=0.40, iou=0.45, stream=True,
        save=False, verbose=False,
    ):
        detections = []
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls.item())
                detections.append({
                    "class_id": class_id,
                    "raw_name": names[class_id],
                    "confidence": float(box.conf.item()),
                    "xyxy": box.xyxy[0].cpu().tolist(),
                })
        print(json.dumps({
            "image": Path(result.path).name,
            "original_shape": list(result.orig_shape),
            "detections": detections,
        }))
PY
```

To make a separately authorized representative-image trial, set `PPE_IMAGES` to an existing reviewed fixture directory and rerun the same Python block:

```sh
export PPE_IMAGES="/absolute/path/to/reviewed/representative-images"
```

The prediction branch deliberately applies no class filter, so extra labels and unexpected outputs remain visible. CPU is the baseline. Image size 640, confidence 0.40 and IoU 0.45 are illustrative settings, not agreed acceptance thresholds. Empty detections are reported as an empty list rather than converted into violations. Printed boxes use Ultralytics' original-image `xyxy` output; compare them with annotations in the same coordinate system. The snippet produces diagnostic detections only, not application compliance states, frame IDs or zone events.

On an import, model-load or prediction error, retain the diagnostic and runtime versions, stop the trial and investigate compatibility/safety separately. Do not silently upgrade the pinned stack or change approval controls to obtain a successful run. A successful load is a runtime-compatibility observation, not a complete model acceptance.

### Assess representative-image predictions

Use licensed, reviewed, annotated images representative of the intended cameras, not only convenient publisher samples. Include people with helmet and vest, no helmet with vest, helmet without vest, neither item, and occluded or ambiguous evidence. Cover distance, lighting, PPE appearance, partial bodies and overlapping people. Different images may demonstrate different classes; all five need not appear in one frame.

For each image, compare actual class IDs, confidences and boxes against annotations. Record missed people, incorrect Person boxes, missed explicit negative-PPE outputs, false positives and duplicate/conflicting outputs. A runtime label named `no-safety vest` is not enough: the trial must show correct detections of that class on appropriately annotated examples. If a class is not observed, that may reflect the fixtures, thresholds or detector quality; it neither proves the class absent nor establishes support.

Do not conclude `no_helmet` from a missing `hardhat` detection, or `no_safety_vest` from a missing `safety vest` detection. Non-detection can result from occlusion, distance or confidence thresholds. Preserve insufficient or contradictory evidence as unknown in later application reasoning.

Record weights revision/hash, software versions, hardware, input manifest, annotations, image size, thresholds and observed outputs. A small image trial is a diagnostic smoke check, not an accuracy benchmark. Quantitative precision/recall and AP50 require an annotated evaluation protocol. The required public annotated 100-clip dataset remains unidentified; these image checks do not replace it.

### Validate compliance and zones separately

The repository has no implemented inference adapter, PPE association/compliance engine or FR-2 geometry, so there is currently no application command that validates those features. The downloader tests use synthetic byte streams and cannot validate them either. The examples above are not implementation of those missing components.

Later authorized application verification must demonstrate correct PPE-center association to direct Person boxes, deterministic handling of overlapping people, and the five outcomes `COMPLIANT`, `HELMET_MISSING`, `VEST_MISSING`, `HELMET_AND_VEST_MISSING` and `UNKNOWN`. Detector outputs alone do not establish these rules. Ambiguous or conflicting evidence must not be forced into a compliance or violation decision.

FR-2 must wait for real-model FR-1 verification. It then requires clip-specific configured polygons, Person bottom center `((x1 + x2) / 2, y2)`, ray-casting point-in-polygon in matching coordinates, and documented boundary/corner behavior. Validate geometry independently and then with annotated clips; a correct polygon calculation cannot compensate for a missed Person or inaccurate box bottom. Authentication and IP allow-listing are also separate application controls, not model classes.

The practical decision is therefore three separate records: exposed runtime taxonomy, representative prediction evidence, and application/evaluation evidence. None automatically approves adoption. This documentation update changes no source code, checkpoint, configured candidate, approval flag or implementation status.

## Representative held-out evaluation methodology

This methodology explains how a later separately authorized evaluation could produce defensible evidence for the provisional Baskarmother candidate. It is not an implementation plan, an executable harness, permission to load weights, or a claim that evaluation has occurred. The exact artifact remains revision `3213ed51de90cbc76e577e6944e84f7c74343526`, `best.pt`, SHA-256 `8714b4b2bbde95b3a07dcdbe873995e34742b5ce628464a4da232721d4691ffe`. Supplied static five-label evidence does not demonstrate detection quality. Accepted exact-weight rights and independent loading-safety clearance remain prerequisites to an authorized runtime evaluation.

### Representative data and annotation ground truth

The evaluation owner must identify the authoritative public 100-clip dataset required by the attachment, rather than assemble an unnamed set and call the requirement complete. Record its provider, source URLs, immutable version, permissions, clip IDs, content hashes, durations, original resolution/FPS and source-video grouping. Describe the intended camera conditions and document actual coverage of distance, lighting, camera angle, PPE appearance, occlusion, partial bodies and overlapping people. Include compliant workers, each explicit missing-PPE condition, ambiguous visibility and empty/background frames that can reveal false positives. Record gaps rather than asserting that public construction footage represents Renewi conditions automatically.

Freeze a deterministic frame-sampling policy with timestamps, frame IDs, sampling rate or selection rule and any seed. Uniform sampling helps avoid cherry-picking easy frames; separately identified challenge samples may examine rare hazards but must not silently alter the primary benchmark. Record clip, frame and eligible object counts. One hundred clips is not one hundred independent sources, and thousands of neighboring frames do not provide thousands of independent observations.

Human annotations must be independent of the candidate's predictions. Define an annotation manual for `person`, `helmet`, `no_helmet`, `safety_vest` and `no_safety_vest`, mapping reviewed source labels to that taxonomy. Specify box extent for each class, including whether negative-PPE boxes cover a head, torso or another region, visible versus full-body Person boxes, truncation, occlusion, minimum visibility and ignore/crowd rules. Resolve these semantics before comparing predictions; a mismatch in box conventions can look like detector failure.

Explicit negative annotations require visibly absent PPE under the agreed protocol, not merely an unannotated or undetected positive item. Mark unobservable helmet/vest evidence as unknown or ignored for the relevant label, with reasons; keep an otherwise visible Person eligible for Person evaluation. Annotate all eligible instances in scored frames, including difficult examples, so incomplete labels do not turn correct predictions into false positives. Use independent second-review and adjudication for a documented subset and all disputed cases; record agreement, corrections and the final annotation version/hash.

Additional person-to-PPE links, per-person compliance labels and clip-specific polygons/inside labels are needed for application evaluation, not object AP alone. These links may use frame-local indices without recognizing workers. Event intervals for zone evaluation are optional supplementary annotations only when their counting rule is agreed; no persistent identity recognition or tracking is introduced.

### Split isolation and leakage limits

Separate development/threshold tuning from the final holdout at the source-group level before extracting frames. Keep every segment, crop, augmentation and adjacent frame from the same underlying video or scene group in one split. Where metadata permits, also isolate shared camera sessions/sites to assess generalization, and document any intentional exception. Stratify source groups for required classes and conditions without breaking their isolation.

Audit overlap against known candidate training and validation sources, not just your local split names. Use file/content hashes for exact duplicates, perceptual similarity for resized/cropped or re-encoded media, and manual review of suspected shared scenes; record methods, exclusions and unresolved matches. Baskarmother's exact training membership and checkpoint-selection history remain unconfirmed, so absence of detected duplicates cannot prove absence of training leakage. State the holdout's independence evidence and residual uncertainty explicitly.

The linked construction image dataset's reported 307/57/34 full split sizes do not establish independence from this checkpoint's training or selection. Its `mini` configuration uses the same archive for all splits and must never be treated as independent train/validation/test evidence. A publisher test archive with unverified checkpoint usage can support exploratory diagnostics, but not an unqualified clean-holdout claim or the public 100-clip requirement.

Freeze the final manifest, annotations, sampling and metric protocol before scoring. Do not select confidence thresholds, NMS settings, image size, candidate checkpoints or favorable subgroups using final-holdout results. Tune on separate development data and record the selection procedure. If final results drive further changes, identify that set as now used for development and obtain a fresh independent holdout for confirmatory evidence.

The attachment does not define whether its 100 clips must all be final test clips or span a larger evaluation corpus. The owner must document that interpretation and actual final-holdout count; do not silently divide the only 100 clips for tuning and claim a 100-clip held-out evaluation. Separate tuning data is needed if all 100 are designated final holdout.

### Frozen run record and detection metrics

A reproducible run record must identify dataset name/version/source, manifest and annotation hashes, split role, leakage review, model name/revision, weight source/size/digest, complete runtime class map and canonical mapping. Record the evaluation date, project Git commit, evaluator version and exact invocation, dependency/runtime versions, device/hardware, preprocessing and coordinate transformations, original/input resolutions, image size, batch size, sampling, confidence settings, NMS IoU and evaluation matching IoU. These are required evidence fields for a future evaluator, not references to an existing evaluation command. The repository currently has no implemented metrics harness.

For detection scoring, use class-compatible one-to-one matching between predictions and eligible ground-truth boxes at box IoU 0.50. Record the evaluator's matching order, interpolation and ignore/crowd conventions. Unmatched eligible annotations are false negatives; unmatched predictions, including duplicate detections, are false positives. Wrong-class predictions ordinarily produce a false positive for the predicted class and leave the true class unmatched. Restore predictions to original-frame coordinates before matching.

At a confidence operating point chosen on development data, precision is `TP / (TP + FP)` and recall is `TP / (TP + FN)`. Report each required class's TP/FP/FN, support, precision and recall; state whether aggregates are micro- or macro-averaged. AP50 is the area under that class's precision-recall curve as confidence varies at matching IoU 0.50. Preserve scores down to a documented sufficiently low evaluator cutoff for AP; scoring only predictions retained at an illustrative 0.40 operating threshold truncates the curve and can reduce measured AP. Keep the selected operational threshold distinct from the AP collection cutoff.

Report each class's AP50 and a clearly named five-required-class overall mAP50. Any additional all-model-class mean must be separately labeled with its included classes. Classes without eligible ground truth have unsupported AP/recall, not proven perfect performance; document undefined-value handling and do not silently omit a required class to raise the mean. Distinguish NMS IoU from matching IoU: they govern different operations. Scores are not calibrated probabilities or accuracy percentages.

Supplement the primary metrics with condition-level breakdowns, support and reviewed error examples. Estimate uncertainty by resampling independent source groups, or clips when clips are independent, rather than treating adjacent frames as independent. State the resampling method/seed and limitations of small or rare-class samples. Persist machine-readable results with provenance and raw predictions/matching records sufficient for auditing, plus a human-readable interpretation. None of these outputs has been produced by this guidance.

### Runtime measurements on the intended local workload

Measure cold model loading/initialization and warm-up separately from steady-state inference. For future authorized measurements, fix and record hardware/device, CPU thread settings, accelerator/backend if used, runtime versions, precision, batch size, input size, clip resolution and sampling policy. Synchronize asynchronous accelerator work around timed regions where relevant; otherwise timings may measure submission rather than completed inference.

Report sample counts, repeated-run variability and p50/p95 latency rather than a single fastest frame. Define detector-only timing explicitly, separating preprocessing, model forward execution and postprocessing if possible. Measure decode-to-structured-result end-to-end latency separately, including frame ingestion, mapping, association, compliance and zone processing only when those components actually exist. Do not label raw model timings as complete application latency.

Report processed frames per second, wall-clock time per clip, peak resident memory and accelerator memory where applicable, failures, dropped frames and backlog growth. Distinguish source-video FPS, configured sampling FPS and actual sustained processing throughput. Sampling fewer frames may improve throughput while missing short incursions; measure that tradeoff in separate task outcomes. The attachment's 640/0.40/0.45/5-FPS examples are settings illustrations, not approved runtime budgets or measured results.

### Separate compliance and FR-2 validation

Object AP50 does not establish correct person-level PPE compliance. With reviewed ground-truth detections, later application validation can isolate configurable mapping, box parsing, PPE-center-within-Person association, deterministic overlap handling and compliance rules. With real predictions on held-out annotated frames, end-to-end evaluation can expose detector misses plus association errors. Report both evidence layers separately; logic-only success is not model accuracy.

Use the five compliance states in a person-level confusion matrix. Report wrong-person association, false violations, missed violations and UNKNOWN frequency with explicit denominators and person-frame matching rules. Count missed Persons separately and in end-to-end coverage, rather than scoring only successfully detected workers. Report UNKNOWN over all eligible matched persons and coverage over all eligible ground-truth persons so abstention cannot conceal missed hazards. Lack of positive PPE evidence must not become an explicit negative class, and contradictory evidence must not be forced into a compliance claim.

FR-2 logic validation separately checks bottom center `((x1 + x2) / 2, y2)`, ray casting, matching box/polygon coordinate systems, clip-specific polygon selection, inside/outside cases, boundary/corner policy, and concave polygons if supported. Validate structured incursion event fields independently. Real-model FR-1 verification remains a prerequisite to FR-2 application acceptance; no Person box may be invented when detection fails.

For end-to-end zone evaluation, compare per-person inside/outside predictions against independently reviewed reference boxes and polygons under the same declared boundary policy. Report missed Persons, bottom-center localization errors near boundaries and geometry/configuration errors separately. Supplement with incursion precision/recall, false alarms and missed incursions using a predeclared unit: person-frame or annotated episode with explicit temporal matching tolerance. Do not count repeated inside-frame events as multiple independent successful incursions. Event-level detection delay and sampling losses are supplementary measures requiring agreed episode semantics, not evidence of a implemented tracking feature. These application modules and measurements do not currently exist.

### Acceptance interpretation and current status

Use separate acceptance records for model detection, local runtime, FR-1 application compliance, FR-2 geometry/events and end-to-end task outcomes. Accepted artifact rights, safe authorized loading, trustworthy architecture/taxonomy and reproducible provenance are eligibility gates, not metrics to average into an accuracy score. Authentication and IP allow-list acceptance remain separate security responsibilities.

Before opening final-holdout results, the PoC/model owner and evaluation owner must approve numerical targets for required-class AP50 and precision/recall, especially Person and explicit negative PPE, and define which scenarios/support counts are mandatory. They must separately agree acceptable false/missed violation rates, UNKNOWN/coverage rates, incursion errors, latency percentiles, sustained throughput and resource budgets on named hardware. Record whether passing depends on point estimates or confidence bounds and how unsupported classes, insufficient support and incomplete provenance are handled. These are proposed decision dimensions, not invented contractual thresholds.

The attachment establishes no numeric accuracy or latency targets. Until those are agreed, a completed run could describe measured performance but cannot establish a quantitative acceptance pass. A strong overall mAP50 must not compensate for a failed mandatory class or application requirement. Likewise, successful synthetic compliance/geometry checks cannot satisfy real-model or 100-clip evaluation gates.

Current status is unchanged: no model is approved; the authoritative public 100-clip dataset, exact training-split lineage, accepted weight rights, runtime results and numerical acceptance targets remain unresolved. This documentation update performs no acquisition, checkpoint loading, inference, evaluation or test execution, changes no approval controls, and creates no implementation plan.

## Dependency and dataset licensing

Licenses must be reviewed separately from weight provenance. Installing a library
does not grant a license to unrelated weights or datasets. Ultralytics is offered
under AGPL-3.0 or an enterprise agreement, **not a permissive license**; see its
[pinned package metadata](https://pypi.org/project/ultralytics/8.3.70/) and
[licensing guidance](https://www.ultralytics.com/license). Project/legal owner
review is required before distribution or nonlocal deployment. The complete
dependency resolution is recorded in `backend/requirements.lock`; this is a
runtime reproducibility record, not a legal approval or security audit.

The authoritative annotated 100-clip evaluation dataset is still unidentified.
No model inference, dataset evaluation, or local accuracy metric is claimed.
Published benchmark values have not been copied into application metrics.

## Approval and recovery

`config/model.yaml` intentionally records `approved: false`, null license fields,
and false checkpoint/capability checks. `scripts/download_model.py` checks all
review fields before network access. Review fields are a version-controlled
human decision, not a cryptographic attestation: restrict who can change them.

Next evidence request belongs to the PoC/model owner and rights reviewer:
obtain a maintainer/rightsholder statement tied to the exact release asset and
digest, covering intended PoC use and upstream pretrained-weight/data
obligations; obtain the release checkpoint's complete ordered class map and
its relationship to the later notebook. Existing issue #1 is the recorded
follow-up location, not a grant of permission. For the fallback, request
weight-specific rights separately from the dataset's CC BY 4.0 declaration.
No permission request was sent by this investigation.

To unblock STEP-01 under the unchanged approved contract, the PoC/model owner
and rights reviewer must provide accepted exact-asset rights and checkpoint
evidence of `person`, `helmet`, `no_helmet`, `safety_vest`, and `no_safety_vest`.
Neither candidate currently has this evidence. If the actual checkpoint cannot
meet that contract, an explicit owner decision and any necessary plan reapproval
are required before a replacement or scope change; this investigation authorizes
neither. A secondary detector, heuristic, invented alias, or absence-based
negative class must not be used to bypass the gate.

After that decision, record the selected immutable revision, source asset,
license evidence/reviewer, actual checkpoint class IDs and names, and expected
size/SHA-256. Safely review any pickle-based checkpoint before loading it:
integrity verification establishes matching bytes, not absence of malicious
code. Re-run download tests, download with the reviewed configuration, verify
the local hash and classes, and complete VAL-01. Model replacement requires a
documented decision and any necessary plan reapproval.

The downloader follows only HTTPS redirects to explicitly allowed public
artifact hosts, bounds download size to provenance, verifies SHA-256 before
atomic replacement, and removes partial temporary files on exceptions.
Existing corrupt files are retained if the replacement fails verification.
It never imports Torch or deserializes a checkpoint. It does not automatically
choose another model.
