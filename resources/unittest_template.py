# flake8: noqa
"""This template is used inside snekbox to evaluate and test user code."""
import ast
import base64
import functools
import io
import sys
import traceback
import typing
import unittest
from itertools import chain
from types import ModuleType, SimpleNamespace
from typing import NoReturn


### USER CODE


class RunnerTestCase(unittest.IsolatedAsyncioTestCase):
### UNIT CODE


normal_exit = False
_EXIT_WRAPPER_TYPE = typing.Callable[[int], None]


def _exit_sandbox(code: int, stdout: io.StringIO, result_writer: io.StringIO) -> NoReturn:
    """
    Exit the sandbox by printing the result to the actual stdout and exit with the provided code.

    Codes:
    - 0: Executed with success
    - 5: Syntax error while parsing user code
    - 6: Uncaught exception while loading user code
    - 99: Internal error

    137 can also be generated by NsJail when killing the process.
    """
    print(result_writer.getvalue(), file=stdout, end="")
    global normal_exit
    normal_exit = True
    sys.exit(code)


def _load_user_module(result_writer, exit_wrapper: _EXIT_WRAPPER_TYPE) -> ModuleType:
    """Load the user code into a new module and return it."""
    code = base64.b64decode(USER_CODE).decode("utf8")
    try:
        ast.parse(code, "<input>")
    except SyntaxError:
        result_writer.write("".join(traceback.format_exception(*sys.exc_info(), limit=0)))
        exit_wrapper(5)

    _module = ModuleType("module")
    exec(code, _module.__dict__)

    return _module


def _main(result_writer: io.StringIO, module: ModuleType, exit_wrapper: _EXIT_WRAPPER_TYPE) -> None:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RunnerTestCase)
    globals()["module"] = module
    result = suite.run(unittest.TestResult())

    result_writer.write(str(int(result.wasSuccessful())))

    if not result.wasSuccessful():
        result_writer.write(
            ";".join(chain(
                (error[0]._testMethodName.removeprefix("test_") for error in result.errors),
                (failure[0]._testMethodName.removeprefix("test_") for failure in result.failures)
            ))
        )

    exit_wrapper(0)


def _entry():
    result_writer = io.StringIO()
    exit_wrapper = functools.partial(_exit_sandbox, stdout=sys.stdout, result_writer=result_writer)

    try:
        # Fake file object not writing anything
        devnull = SimpleNamespace(write=lambda *_: None, flush=lambda *_: None)

        # stdout/err is patched in order to control what is outputted by the runner
        sys.__stdout__ = sys.stdout = devnull
        sys.__stderr__ = sys.stderr = devnull

        # Load the user code as a global module variable
        try:
            module = _load_user_module(result_writer, exit_wrapper)
        except BaseException as e:
            result_writer.write(f"Uncaught exception while loading user code: {e}")
            exit_wrapper(6)

        _main(result_writer, module, exit_wrapper)
    except BaseException as e:
        if isinstance(e, SystemExit) and normal_exit:
            raise e from None
        result_writer.write(f"Uncaught exception inside runner: {e}")
        exit_wrapper(99)

_entry()
