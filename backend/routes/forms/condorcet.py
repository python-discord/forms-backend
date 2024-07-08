"""Calculate the condorcet winner for a given question on a poll."""

from condorcet import CondorcetEvaluator
from pydantic import BaseModel
from spectree import Response
from starlette import exceptions
from starlette.authentication import requires
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend import discord
from backend.models.dtos import Form, FormResponse, Question
from backend.route import Route
from backend.validation import api


class CondorcetResponse(BaseModel):
    question: Question
    winners: list[str]
    rest_of_table: dict


class InvalidCondorcetRequest(exceptions.HTTPException):
    """The request for a condorcet calculation was invalid."""


def reprocess_vote_object(vote: dict[str, int | None], number_options: int) -> dict[str, int]:
    """Reprocess votes so all no-preference votes are re-ranked as last (equivalent in Condorcet)."""
    vote_object = {}

    for option, score in vote.items():
        vote_object[option] = score or number_options

    return vote_object


class Condorcet(Route):
    """Run a condorcet calculation on the given question on a form."""

    name = "form_condorcet"
    path = "/{form_id:str}/condorcet/{question_id:str}"

    @requires(["authenticated"])
    @api.validate(
        resp=Response(HTTP_200=CondorcetResponse),
        tags=["forms", "responses", "condorcet"],
    )
    async def get(self, request: Request) -> JSONResponse:
        """
        Run and return the condorcet winner for a poll.

        Optionally takes a `?winners=` parameter specifying the number of winners to calculate.
        """
        form_id = request.path_params["form_id"]
        question_id = request.path_params["question_id"]
        num_winners = request.query_params.get("winners", "1")

        try:
            num_winners = int(num_winners)
        except ValueError:
            raise InvalidCondorcetRequest(detail="Invalid number of winners", status_code=400)

        await discord.verify_response_access(form_id, request)

        # We can assume we have a form now because verify_response_access
        # checks for form existence.
        form_data = Form(**(await request.state.db.forms.find_one({"_id": form_id})))

        questions = [question for question in form_data.questions if question.id == question_id]

        if len(questions) != 1:
            raise InvalidCondorcetRequest(detail="Question not found", status_code=400)

        question = questions[0]

        if num_winners > len(question.data["options"]):
            raise InvalidCondorcetRequest(
                detail="Requested more winners than there are candidates", status_code=400
            )

        if question.type != "vote":
            raise InvalidCondorcetRequest(
                detail="Requested question is not a condorcet vote component", status_code=400
            )

        cursor = request.state.db.responses.find(
            {"form_id": form_id},
        )
        responses = [FormResponse(**response) for response in await cursor.to_list(None)]

        votes = [
            reprocess_vote_object(response.response[question_id], len(question.data["options"]))
            for response in responses
        ]

        evaluator = CondorcetEvaluator(candidates=question.data["options"], votes=votes)

        winners, rest_of_table = evaluator.get_n_winners(num_winners)

        return JSONResponse({
            "question": question.dict(),
            "winners": winners,
            "rest_of_table": rest_of_table,
        })
