#!/usr/bin/env python
"""Run the APTRA QA/QC suite with a compact, readable report."""

import logging
import re
import sys
import time
import traceback
import unittest
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


class ReadableTestResult(unittest.TestResult):
    """Collect results for grouped output instead of printing one long stream."""

    def __init__(self):
        super().__init__()
        self.records = []
        self._started_at = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._started_at = time.perf_counter()

    def _record(self, test, status, detail=""):
        duration = time.perf_counter() - self._started_at
        self.records.append((test, status, duration, detail))

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "FAIL", "".join(traceback.format_exception(*err)))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "ERROR", "".join(traceback.format_exception(*err)))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "SKIP", reason)


def readable_name(value: str) -> str:
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    value = value.replace("_", " ").strip()
    return value.replace("Llm", "LLM").replace("Ui", "UI")


def run_tests() -> int:
    loader = unittest.TestLoader()
    suite = loader.discover(str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    result = ReadableTestResult()

    # Expected-error route tests deliberately log errors. Unexpected exceptions
    # remain visible below as test failures or errors.
    logging.disable(logging.CRITICAL)
    started_at = time.perf_counter()
    try:
        suite.run(result)
    finally:
        logging.disable(logging.NOTSET)
    elapsed = time.perf_counter() - started_at

    grouped = defaultdict(list)
    for record in result.records:
        grouped[record[0].__class__.__name__].append(record)

    print("\nAPTRA TEST REPORT")
    print("=" * 72)
    for class_name, records in grouped.items():
        print(f"\n{readable_name(class_name)}")
        print("-" * 72)
        for test, status, duration, _ in records:
            description = test.shortDescription() or readable_name(test._testMethodName)
            print(f"  [{status:<5}] {description:<54} {duration:>6.3f}s")

    problems = [record for record in result.records if record[1] in {"FAIL", "ERROR"}]
    if problems:
        print("\nFAILURE DETAILS")
        print("=" * 72)
        for test, status, _, detail in problems:
            print(f"\n[{status}] {test.id()}\n{detail.rstrip()}")

    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    passed = result.testsRun - failed - errors - skipped

    print("\nSUMMARY")
    print("=" * 72)
    print(
        f"  Total: {result.testsRun}  |  Passed: {passed}  |  Failed: {failed}  "
        f"|  Errors: {errors}  |  Skipped: {skipped}"
    )
    print(f"  Time:  {elapsed:.3f}s")
    print("\nRESULT: ALL TESTS PASSED" if result.wasSuccessful() else "\nRESULT: TESTS FAILED")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
