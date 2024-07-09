import base64
from itertools import count
from pathlib import Path
from textwrap import indent
from typing import NamedTuple

import httpx
from httpx import HTTPStatusError

from backend.constants import SNEKBOX_URL
from backend.models import Form, FormResponse

with Path("resources/unittest_template.py").open(encoding="utf8") as file:
    TEST_TEMPLATE = file.read()


class BypassDetectedError(Exception):
    """Detected an attempt at bypassing the unittests."""


class UnittestResult(NamedTuple):
    question_id: str
    question_index: int
    return_code: int
    passed: bool
    result: str


def _make_unit_code(units: dict[str, str]) -> str:
    """Compose a dict mapping unit names to their code into an actual class body."""
    result = ""

    for unit_name, unit_code in units.items():
        # Function definition
        if unit_name == "setUp":
            result += "\ndef setUp(self):"
        elif unit_name == "tearDown":
            result += "\ndef tearDown(self):"
        else:
            name = f"test_{unit_name.removeprefix("#").removeprefix("test_")}"
            result += f"\nasync def {name}(self):"

        # Unite code
        result += f"\n{indent(unit_code, "    ")}"

    return indent(result, "    ")


def _make_user_code(code: str) -> str:
    """Compose the user code into an actual base64-encoded string variable."""
    code = base64.b64encode(code.encode("utf8")).decode("utf8")
    return f'USER_CODE = b"{code}"'


async def _post_eval(code: str) -> dict[str, str]:
    """Post the eval to snekbox and return the response."""
    async with httpx.AsyncClient() as client:
        data = {"input": code}
        response = await client.post(SNEKBOX_URL, json=data, timeout=10)

        response.raise_for_status()
        return response.json()


async def execute_unittest(
    form_response: FormResponse,
    form: Form,
) -> tuple[list[UnittestResult], list[BypassDetectedError]]:
    """Execute all the unittests in this form and return the results."""
    unittest_results = []
    errors = []

    for index, question in enumerate(form.questions):
        if question.type == "code":
            # Exit early if the suite doesn't have any tests
            if question.data["unittests"] is None:
                unittest_results.append(
                    UnittestResult(
                        question_id=question.id,
                        question_index=index,
                        return_code=0,
                        passed=True,
                        result="",
                    )
                )
                continue

            passed = False

            # Tests starting with an hashtag should have censored names.
            hidden_test_counter = count(1)
            hidden_tests = {
                test.removeprefix("#").removeprefix("test_"): next(hidden_test_counter)
                for test in question.data["unittests"]["tests"]
                if test.startswith("#")
            }

            # Compose runner code
            unit_code = _make_unit_code(question.data["unittests"]["tests"])
            user_code = _make_user_code(form_response.response[question.id])

            code = TEST_TEMPLATE.replace("### USER CODE", user_code)
            code = code.replace("### UNIT CODE", unit_code)

            try:
                try:
                    response = await _post_eval(code)
                except HTTPStatusError:
                    return_code = 99
                    result = "Unable to contact code runner."
                else:
                    return_code = int(response["returncode"])

                    # Parse the stdout if the tests ran successfully
                    if return_code == 0:
                        stdout = response["stdout"]
                        try:
                            passed = bool(int(stdout[0]))
                        except ValueError:
                            msg = "Detected a bypass when reading result code."
                            raise BypassDetectedError(msg)

                        if passed and stdout.strip() != "1":
                            # Most likely a bypass attempt
                            # A 1 was written to stdout to indicate success,
                            # followed by the actual output
                            msg = "Detected improper value for stdout in unittest."
                            raise BypassDetectedError(msg)

                        # If the test failed, we have to populate the result string.
                        if not passed:
                            failed_tests = stdout[1:].strip().split(";")

                            # Redact failed hidden tests
                            for i, failed_test in enumerate(failed_tests.copy()):
                                if failed_test in hidden_tests:
                                    failed_tests[i] = f"hidden_test_{hidden_tests[failed_test]}"

                            result = ";".join(failed_tests)
                        else:
                            result = ""
                    elif return_code in {5, 6, 99}:
                        result = response["stdout"]
                    # Killed by NsJail
                    elif return_code == 137:
                        return_code = 7
                        result = "Timed out or ran out of memory."
                    # Another code has been returned by CPython because of another failure.
                    else:
                        return_code = 99
                        result = "Internal error."
            except BypassDetectedError as error:
                return_code = 10
                result = "Bypass attempt detected, aborting."
                errors.append(error)
                passed = False

            unittest_results.append(
                UnittestResult(
                    question_id=question.id,
                    question_index=index,
                    return_code=return_code,
                    passed=passed,
                    result=result,
                )
            )

    return unittest_results, errors
