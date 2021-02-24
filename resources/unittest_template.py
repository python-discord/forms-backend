# flake8: noqa
"""This template is used inside snekbox to evaluate and test user code."""
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


def _exit_sandbox(code: int) -> NoReturn:
    """
    Exit the sandbox by printing the result to the actual stdout and exit with the provided code.

    Codes:
    - 0: Executed with success
    - 5: Syntax error while parsing user code
    - 99: Internal error
    """
    print(RESULT.getvalue(), file=ORIGINAL_STDOUT, end="")
    sys.exit(code)


def _load_user_module() -> ModuleType:
    """Load the user code into a new module and return it."""
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
    # Fake file object not writing anything
    DEVNULL = SimpleNamespace(write=lambda *_: None, flush=lambda *_: None)

    RESULT = io.StringIO()
    ORIGINAL_STDOUT = sys.stdout

    # stdout/err is patched in order to control what is outputted by the runner
    sys.stdout = DEVNULL
    sys.stderr = DEVNULL
    
    # Load the user code as a global module variable
    module = _load_user_module()
    _main()
except Exception:
    print("Uncaught exception:\n", file=RESULT)
    traceback.print_exc(file=RESULT)
    _exit_sandbox(99)