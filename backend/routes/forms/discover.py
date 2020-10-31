"""
Return a list of all publicly discoverable forms to unauthenticated users.
"""

from starlette.responses import JSONResponse

from backend.route import Route


class DiscoverableFormsList(Route):
    """
    List all discoverable forms that should be shown on the homepage.
    """

    name = "discoverable_forms_list"
    path = "/discoverable"

    async def get(self, request):
        forms = []

        for form in request.state.db.forms.find({
            "discoverable": True
        }):
            form["_id"] = str(form["_id"])
            forms.append(form)

        return JSONResponse(
            forms
        )
