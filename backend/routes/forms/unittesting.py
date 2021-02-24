import ast
from collections import namedtuple
from textwrap import indent
from typing import Optional

import httpx

from backend.constants import SNEKBOX_URL
from backend.models import FormResponse, Form

with open("resources/unittest_template.py") as file:
    TEST_TEMPLATE = file.read()


UnittestResult = namedtuple("UnittestResult", "question_id return_code passed result")


def _make_unit_code(units: dict[str, str]) -> str:
    result = ""

    for unit_name, unit_code in units.items():
        result += f"\ndef test_{unit_name}(unit):\n{indent(unit_code, '    ')}"

    return indent(result, "    ")


def _make_user_code(code: str) -> str:
    # Make sure that we we escape triple quotes and backslashes in the user code
    code = code.replace('"""', '\\"""').replace("\\", "\\\\")
    return f'USER_CODE = """{code}"""'


async def _post_eval(code: str) -> Optional[dict[str, str]]:
    data = {"input": code}
    async with httpx.AsyncClient() as client:
        response = await client.post(SNEKBOX_URL, json=data)

        if not response.status_code == 200:
            return

        return response.json()


async def execute_unittest(form_response: FormResponse, form: Form) -> list[UnittestResult]:
    unittest_results = []

    for question in form.questions:
        if question.type == "code" and "unittests" in question.data:
            passed = False

            unit_code = _make_unit_code(question.data["unittests"])
            user_code = _make_user_code(form_response.response[question.id])

            code = TEST_TEMPLATE.replace("### USER CODE", user_code)
            code = code.replace("### UNIT CODE", unit_code)

            # Make sure that the code is well formatted (we don't check for the user code)
            try:
                ast.parse(code)
            except SyntaxError:
                return_code = 99
                result = "Invalid generated unit code."

            else:
                response = await _post_eval(code)

                if not response:
                    return_code = 99
                    result = "Unable to contact code runner."
                else:
                    return_code = int(response["returncode"])

                    if return_code not in (0, 5, 99):
                        return_code = 99
                        result = "Internal error."
                    else:
                        stdout = response["stdout"]
                        passed = bool(int(stdout[0]))

                        if not passed:
                            result = stdout[1:].strip()
                        else:
                            result = ""

            unittest_results.append(UnittestResult(
                question_id=question.id,
                return_code=return_code,
                passed=passed,
                result=result
            ))

    return unittest_results
