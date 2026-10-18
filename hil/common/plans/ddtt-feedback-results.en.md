# DDTT development cycle results

Date: 2026-10-10. Module v0.4.0 (`9c3ff2d`), Windows/ST-Link/OpenOCD 0.12.0.

Requirement: an ADC notification timeout sets diagnostic code 6 before platform_error.
Both boards returned 0 before the fix and 6 afterwards. The new scenario was unchanged:
it disables the DMA IRQ, verifies at least 100 ticks and no publication.
The existing suppressed-callback expectation also changes from 0 to 6: this is the new application
diagnostic contract, not a workaround for the new test. Platform codes 1..5 are preserved.

F411CE and F401CC: 23/23 host, 22/22 hardware scenarios each; BOOT/GPIO recovery 2/2 PASS each.
GCC 13.3.1, GDB 14.2.90.20240526-git/Python 3.11.4.
One initial prepare with `-j 2` reported an output-directory validation ERROR; the sequential
repeat passed 23/23. Its cause is not isolated; the original log is retained. This observation
is unrelated to the firmware defect and is not counted as baseline red-test evidence.

| Build | Run ID | Verdict | Checks | ELF SHA-256 |
| --- | --- | --- | --- | --- |
| ddtt-baseline-f401cc | 20261010T113716.009730Z-HW_ADC_TIMEOUT_DIAGNOSTIC-23520 | FAIL | 10 | `565e3b6f45a1342349bf60a579f70edb0367f15624c3be7a9658e960432c9a6f` |
| ddtt-baseline-f411ce | 20261010T113713.036526Z-HW_ADC_TIMEOUT_DIAGNOSTIC-31616 | FAIL | 10 | `f6d123fa7d44b8f3cfa1350c470cd4400d1d8ff4f851425cc083558e021f7e7e` |
| ddtt-candidate-f401cc | 20261010T114032.816360Z-HW_ADC_TIMEOUT_DIAGNOSTIC-41936 | PASS | 10 | `584da85c458dbf53ecca2251434d1d60e17fb00041973710eef0728c4d03d408` |
| ddtt-candidate-f411ce | 20261010T113830.915686Z-HW_ADC_TIMEOUT_DIAGNOSTIC-9628 | PASS | 10 | `8a5953acc3aa18e2677062e8e04fbbda1d1ab201380a2bbc6cb2f3397291b352` |
| ddtt-candidate-f411ce | 20261010T113929.784043Z-HW_ADC_TIMEOUT_DIAGNOSTIC-33508 | PASS | 10 | `8a5953acc3aa18e2677062e8e04fbbda1d1ab201380a2bbc6cb2f3397291b352` |

Local evidence (not shipped in Git): `build/ddtt-feedback/` contains selection, export/index,
integrity.json, HTML report, hardware-summary.json and hashed baseline-inputs.
`build/ddtt-baseline-*` retains original ELF files and attempts; `build/ddtt-candidate-*` retains fixes.
Export, integrity verification and report generation have outcomes separate from scenario verdicts.
Boards are left with corrected firmware; reset_run is confirmed. This run does not establish
external electrical measurements or unattended operation of qwen/pi.

## Offline verification

Docker `ci/run_cmsis_checks.py --prepare-jobs 1`: Debug/Release/HIL for both boards — 6 builds,
host 23/23 per board and native-adc 1/1 PASS.
All scenario style checks passed. Export/verify/report returned code 0, including retained FAIL/ERROR.
These checks use a hashed working snapshot, not GitHub CI; the owner performs push and land.

clang-format 18 passed for the modified app.h/program.cpp. A full src check found pre-existing formatting at startup.c line 54; that unchanged file is deferred separately from the functional fix.
