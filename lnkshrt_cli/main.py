from pathlib import Path
from typing import Annotated
from urllib.parse import urljoin, urlsplit

import typer
from rich import print
from tomlkit import dump, load

from lnkshrt_cli.config import INSTANCE_URL, SETTINGS_FILE
from lnkshrt_cli.utils import create_link, create_qr_code, create_token, delete_link, register_user

ALLOWED_SCHEMES = {"http", "https"}
INSTANCE_URL_HELP_TEXT = (
    "The URL of the instance to use for shortening links."
    "If invoked without any value, the instance URL will be reset to the default."
)
app = typer.Typer(no_args_is_help=True, pretty_exceptions_show_locals=False)


@app.command()
def signup(
    username: Annotated[str, typer.Option()],
    email: Annotated[str, typer.Option()],
    password: Annotated[str, typer.Option(prompt=True, confirmation_prompt=True, hide_input=True)],
) -> None:
    """Create a new user account."""
    print(register_user(username, password, email))


@app.command()
def login(
    username: Annotated[str, typer.Option()],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True)],
) -> None:
    """Authenticate with an existing user account."""
    token = create_token(username, password)
    with open(SETTINGS_FILE, "r") as f:
        configuration = load(f)
    configuration["authentication"]["token"] = token
    with open(SETTINGS_FILE, "w") as f:
        dump(configuration, f)


@app.command()
def create(
    url: Annotated[str, typer.Argument(help="The original URL to be shortened.")],
    custom_path: Annotated[
        str, typer.Option(help="Specify a custom path for the shortened URL.")
    ] = "",
    generate_qr_code: Annotated[
        str,
        typer.Option(
            help="If provided, generate a QR code for the shortened URL"
            "The generated QR code image will be saved to the specified location."
        ),
    ] = "",
) -> None:
    """Create a shortened URL."""
    custom_path = custom_path or None
    short_url = create_link(url, custom_path)
    link = urljoin(INSTANCE_URL, short_url)
    print(f"[yellow]link:[/] {link}")

    if generate_qr_code:
        destination = Path(generate_qr_code)
        try:
            destination.mkdir(parents=True, exist_ok=True)  # Making sure the path exists.
        except PermissionError:
            print(
                "[red]Unable to save the QR code image."
                "Please check the specified path and ensure you have the necessary permissions."
            )
            raise typer.Exit(1)
        destination = destination.joinpath(short_url + ".png").absolute()
        create_qr_code(link, str(destination))
        print(f"QR code saved at {destination}")


@app.command()
def delete(url: Annotated[str, typer.Argument(help="The original URL to be shortened.")]) -> None:
    """Delete a shortened URL."""
    print(delete_link(url))


@app.command(no_args_is_help=True)
def config(
    instance_url: Annotated[str, typer.Option(help=INSTANCE_URL_HELP_TEXT)] = "",
    token: Annotated[
        str, typer.Option(help="Set the authentication token to be used for API access.")
    ] = "",
) -> None:
    """Configure lnkshrt settings."""
    with open(SETTINGS_FILE, "r") as f:
        configuration = load(f)
    updated = []
    if instance_url:
        scheme = urlsplit(instance_url).scheme
        if scheme == "":
            print(
                "URL scheme is missing. Please include 'http://' or 'https://' "
                "at the beginning of the URL.   "
            )
            raise typer.Abort()
        elif scheme not in ALLOWED_SCHEMES:
            print("Invalid URL scheme. Only 'http://' and 'https://' schemes are allowed.")
            raise typer.Abort()
        configuration["custom"]["instance_url"] = instance_url
        updated.append("instance URL")

    if token:
        configuration["authentication"]["token"] = token
        updated.append("token")

    if updated:
        with open(SETTINGS_FILE, "w") as f:
            dump(configuration, f)
            print(f"Configuration updated successfully: {', '.join(updated)}")
    else:
        print("No configuration changes were made.")
