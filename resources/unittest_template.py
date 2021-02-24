# flake8: noqa
import ast
import io
import os
import sys
import traceback
import unittest
from itertools import chain
from types import ModuleType, SimpleNamespace
from typing import NoReturn
from unittest import mock

### USER CODE


class RunnerTestCase(unittest.TestCase):
### UNIT CODE


# Fake file object not writing anything
DEVNULL = SimpleNamespace(write=lambda *_: None, flush=lambda *_: None)

RESULT = io.StringIO()
ORIGINAL_STDOUT = sys.stdout

sys.stdout = DEVNULL
sys.stderr = DEVNULL


def _exit_sandbox(code: int) -> NoReturn:
    """
    Codes:
    - 0: Executed with success
    - 5: Syntax error while parsing user code
    - 99: Internal error
    """
    result_content = RESULT.getvalue()

    print(
        f"{result_content}",
        file=ORIGINAL_STDOUT
    )
    sys.exit(code)


def _load_user_module() -> ModuleType:
    try:
        ast.parse(USER_CODE, "<input>")
    except SyntaxError:
        RESULT.write("".join(traceback.format_exception(*sys.exc_info(), limit=0)))
        _exit_sandbox(5)

    _module = ModuleType("module")
    exec(USER_CODE, _module.__dict__)

    return _module


def _main() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RunnerTestCase)
    result = suite.run(unittest.TestResult())

    RESULT.write(str(int(result.wasSuccessful())))

    if not result.wasSuccessful():
        RESULT.write(
            ";".join(chain(
                (error[0]._testMethodName.lstrip("test_") for error in result.errors),
                (failure[0]._testMethodName.lstrip("test_") for failure in result.failures)
            ))
        )

    _exit_sandbox(0)


try:
    module = _load_user_module()
    _main()
except Exception:
    print("Uncaught exception:\n", file=RESULT)
    traceback.print_exc(file=RESULT)
    _exit_sandbox(99)
