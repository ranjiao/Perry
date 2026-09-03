#!/usr/bin/env python3
"""TASK-325 mutation harness.

Rules this harness follows, each because this project has paid for its absence:

* **Anchor by line number WITH an assert on the old text.** A non-matching
  anchor silently no-ops and reports a meaningless OK.
* **Restore from bytes snapshotted BEFORE the mutation, and verify the restore
  against `git show HEAD:<path>` — an INDEPENDENT source.** TASK-256 records
  that comparing a restored file to the bytes the harness itself just wrote is
  circular and proves nothing. The code under mutation is committed at HEAD,
  so git is the outside witness.
* **Clear `__pycache__` and cross the whole-second boundary** before running,
  or Python serves a stale `.pyc` and the mutation appears green.
* **A GREEN mutation is the finding**, and is reported as one rather than
  retried.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/bytedance/proj/Perry/.claude/worktrees/agent-a5396aeb60307b5e7")

# (label, file, 1-based line, must-contain-in-that-line, replacement, module, test)
MUTATIONS = [
    ("M1 missing-rule never fires", "bin/lib/__init__.py",
     "    if not s:", "    if False:",
     "test_summary_is_asked_for",
     "TestTheLinterReportsWhatTheWriterRefuses.test_it_fires_on_a_blank_row_and_names_it"),

    ("M2 repeats-title rule removed", "bin/lib/__init__.py",
     "        if fs == ft or ((fs.startswith(ft) or ft.startswith(fs))",
     "        if False and ((fs.startswith(ft) or ft.startswith(fs))",
     "test_summary_is_asked_for",
     "TestAddRefusesWithoutASummary.test_add_refuses_a_summary_that_is_only_the_title_again"),

    ("M3 no-sentence rule removed", "bin/lib/__init__.py",
     "    if not _SUMMARY_SENTENCE.search(s):", "    if False:",
     "test_summary_is_asked_for",
     "TestAddRefusesWithoutASummary.test_add_refuses_a_fragment_and_a_value_with_no_sentence"),

    ("M4 fragment floor removed", "bin/lib/__init__.py",
     "    if summary_tokens(s) < SUMMARY_MIN_WORDS:", "    if False:",
     "test_summary_is_asked_for",
     "TestAddRefusesWithoutASummary.test_add_refuses_a_fragment_and_a_value_with_no_sentence"),

    ("M5 add's required-summary refusal removed", "bin/perry-task",
     "    if not args.summary or not args.summary.strip():", "    if False:",
     "test_summary_is_asked_for",
     "TestAddRefusesWithoutASummary.test_add_refuses_when_summary_is_absent"),

    ("M6 add's shape refusal removed", "bin/perry-task",
     "    if _shape:", "    if False:",
     "test_summary_is_asked_for",
     "TestAddRefusesWithoutASummary.test_add_refuses_a_summary_that_is_only_the_title_again"),

    ("M7 rewrite writer's shape gate removed", "bin/perry-task",
     "    if not args.clear:", "    if False:",
     "test_summary_is_asked_for",
     "TestTheRewriteWriterHoldsTheSameLine.test_summary_refuses_a_second_title"),

    ("M8 check dropped from the DEFAULT pass", "bin/perry-lint",
     "            findings.extend(check_summaries(root)[:DRIFT_ROWS_SHOWN])",
     "            findings.extend([])",
     "test_summary_is_asked_for",
     "TestTheLinterReportsWhatTheWriterRefuses.test_the_default_pass_reports_it_without_being_asked"),

    ("M9 closed rows scanned too", "bin/perry-lint",
     "        if isinstance(status, str) and status in closed:",
     "        if False:",
     "test_summary_is_asked_for",
     "TestTheLinterReportsWhatTheWriterRefuses.test_closed_rows_are_not_scanned"),

    ("M10 findings promoted to error", "bin/perry-lint",
     "                \"warn\", \"tasks.jsonl\", rule,",
     "                \"error\", \"tasks.jsonl\", rule,",
     "test_summary_is_asked_for",
     "TestTheLinterReportsWhatTheWriterRefuses.test_it_stays_advisory_and_never_makes_the_run_red"),

    ("M11 CONTROL: check flags every summary", "bin/lib/__init__.py",
     "    out: list[tuple[str, str]] = []",
     "    out: list[tuple[str, str]] = [(\"summary-missing\", \"x\")]",
     "test_summary_is_asked_for",
     "TestTheLinterReportsWhatTheWriterRefuses.test_it_is_silent_on_a_good_summary"),
]


def git_bytes(rel):
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                       capture_output=True)
    assert r.returncode == 0, f"git show failed for {rel}"
    return r.stdout


def clear_pycache():
    for d in ROOT.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


def run_test(module, test):
    return subprocess.run(
        [sys.executable, "-m", "unittest", f"tests.{module}.{test}", "-v"],
        cwd=ROOT, capture_output=True, text=True)


def main():
    results = []
    for label, rel, needle, repl, module, test in MUTATIONS:
        path = ROOT / rel
        # Snapshot BEFORE the mutation, and independently from git.
        before = path.read_bytes()
        witness = git_bytes(rel)
        if before != witness:
            print(f"!! {label}: working tree differs from HEAD for {rel}; "
                  f"the git witness is not usable. SKIPPED.")
            results.append((label, "SKIPPED", ""))
            continue

        text = before.decode()
        if text.count(needle) != 1:
            print(f"!! {label}: anchor {needle!r} occurs "
                  f"{text.count(needle)} times in {rel} — NOT 1. "
                  f"A non-matching anchor is a silent no-op. SKIPPED.")
            results.append((label, "BAD ANCHOR", ""))
            continue

        path.write_bytes(text.replace(needle, repl).encode())
        clear_pycache()
        # Cross the whole-second boundary so the mtime actually changes.
        time.sleep(1.1)
        r = run_test(module, test)
        verdict = "RED (good)" if r.returncode != 0 else "GREEN — FINDING"

        # Restore from the PRE-mutation bytes, then verify against git.
        path.write_bytes(before)
        clear_pycache()
        time.sleep(1.1)
        assert path.read_bytes() == git_bytes(rel), \
            f"{label}: RESTORE FAILED for {rel}"

        tail = (r.stdout + r.stderr).strip().split("\n")[-1][:90]
        results.append((label, verdict, tail))
        print(f"{verdict:<18} {label}")

    print("\n" + "=" * 72)
    red = sum(1 for _, v, _ in results if v.startswith("RED"))
    green = sum(1 for _, v, _ in results if v.startswith("GREEN"))
    other = len(results) - red - green
    for label, verdict, tail in results:
        print(f"  {verdict:<18} {label}\n{'':22}{tail}")
    print(f"\n{len(results)} planted · {red} red · {green} GREEN · {other} not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
