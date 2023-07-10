from typing import Annotated
from uuid import UUID

import typer
from api_utils import register_user

app = typer.Typer(pretty_exceptions_show_locals=False)


@app.command()
def signup(
    username: Annotated[str, typer.Option()],
    email: Annotated[str, typer.Option()],
    password: Annotated[str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)],
) -> None:
    """Create a new user account."""
    print(register_user(username, password, email))


@app.command()
def login(token: Annotated[UUID, typer.Option()]) -> None:
    """Authenticate with an existing user account."""
    raise NotImplementedError


@app.command()
def create(url: str, custom_url: Annotated[str, typer.Option()] = "") -> None:
    """Create a shortened url."""
    raise NotImplementedError
