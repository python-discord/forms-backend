import ast
from collections import namedtuple
from itertools import count
from textwrap import indent
from typing import Optional

import httpx

from backend.constants import SNEKBOX_URL
from backend.models import FormResponse, Form

with open("resources/unittest_template.py") as file:
    TEST_TEMPLATE = file.read()


UnittestResult = namedtuple("UnittestResult", "question_id return_code passed result")


def filter_unittests(form: Form) -> Form:
    """
    Replace the unittest data section of code questions with the number of test cases.

    This is used to redact the exact tests when sending the form back to the frontend.
    """
    for question in form.questions:
        if question.type == "code" and "unittests" in question.data:
            question.data["unittests"] = len(question.data["unittests"])

    return form


def _make_unit_code(units: dict[str, str]) -> str:
    """Compose a dict mapping unit names to their code into an actual class body."""
    result = ""

    for unit_name, unit_code in units.items():
        result += f"\ndef test_{unit_name.lstrip('#')}(unit):\n{indent(unit_code, '    ')}"

    return indent(result, "    ")


def _make_user_code(code: str) -> str:
    """Compose the user code into an actual string variable."""
    # Make sure that we we escape triple quotes in the user code
    code = code.replace('"""', '\\"""')
    return f'USER_CODE = r"""{code}"""'


async def _post_eval(code: str) -> Optional[dict[str, str]]:
    """Post the eval to snekbox and return the response."""
    async with httpx.AsyncClient() as client:
        data = {"input": code}
        response = await client.post(SNEKBOX_URL, json=data)

        if not response.status_code == 200:
            return

        return response.json()


async def execute_unittest(form_response: FormResponse, form: Form) -> list[UnittestResult]:
    """Execute all the unittests in this form and return the results."""
    unittest_results = []

    for question in form.questions:
        if question.type == "code" and "unittests" in question.data:
            passed = False

            # Tests starting with an hashtag should have censored names.
            hidden_test_counter = count(1)
            hidden_tests = {
                test.lstrip("#"): next(hidden_test_counter)
                for test in question.data["unittests"].keys()
                if test.startswith("#")
            }

            # Compose runner code
            unit_code = _make_unit_code(question.data["unittests"])
            user_code = _make_user_code(form_response.response[question.id])

            code = TEST_TEMPLATE.replace("### USER CODE", user_code)
            code = code.replace("### UNIT CODE", unit_code)

            # Make sure that the code is well formatted (we don't check for the user code).
            try:
                ast.parse(code)
            except SyntaxError:
                return_code = 99
                result = "Invalid generated unit code."
            # The runner is correctly formatted, we can run it.
            else:
                response = await _post_eval(code)

                if not response:
                    return_code = 99
                    result = "Unable to contact code runner."
                else:
                    return_code = int(response["returncode"])

                    # Another code has been returned by CPython because of another failure.
                    if return_code not in (0, 5, 6, 99):
                        return_code = 99
                        result = "Internal error."
                    else:
                        # Parse the stdout if the tests ran successfully
                        if return_code == 0:
                            stdout = response["stdout"]
                            passed = bool(int(stdout[0]))

                            # If the test failed, we have to populate the result string.
                            if not passed:
                                failed_tests = stdout[1:].strip().split(";")

                                # Redact failed hidden tests
                                for i, failed_test in enumerate(failed_tests[:]):
                                    if failed_test in hidden_tests:
                                        failed_tests[i] = f"hidden_test_{hidden_tests[failed_test]}"

                                result = ";".join(failed_tests)
                            else:
                                result = ""
                        else:
                            result = response["stdout"]

            unittest_results.append(UnittestResult(
                question_id=question.id,
                return_code=return_code,
                passed=passed,
                result=result
            ))

    return unittest_results
