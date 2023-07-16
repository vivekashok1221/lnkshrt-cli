import typing
from urllib.parse import urljoin, urlsplit

import httpx
import qrcode
import typer
from httpx import ConnectError, HTTPStatusError
from loguru import logger
from rich import print

from lnkshrt_cli.config import INSTANCE_URL, TOKEN

ALLOWED_SCHEMES = {"http", "https"}


def _send_request(
    method: str,
    endpoint: str,
    json: dict[str, typing.Any] | None = None,
    data: dict[str, typing.Any] | None = None,
    headers: dict[str, str] | None = None,
    base_url: str | None = None,
) -> dict[str, typing.Any] | bool:
    if base_url is None:
        base_url = INSTANCE_URL
    if headers:
        auth_header = headers.get("Authorization")
        if auth_header:
            token = auth_header.removeprefix("Bearer ")
            if not token:
                print(
                    "Authentication token is missing. "
                    "Please log in using 'lnkshrt login' to generate a token."
                )
                raise typer.Abort()
    try:
        with httpx.Client() as client:
            response = client.request(
                method=method,
                url=urljoin(base_url, endpoint),
                json=json,
                data=data,
                headers=headers,
            )
    except ConnectError:
        print(
            f"[yellow]Warning: Unable to establish a connection to the API at {base_url}. "
            "Please ensure that the URL is correct and the API is accessible."
        )
        return False
    except Exception as e:
        logger.error("An unexpected error occurred.")
        print(e)
        raise typer.Abort()

    try:
        response.raise_for_status()
        return response.json()
    except HTTPStatusError:
        error_detail = response.json()["detail"]
        if response.status_code == 422:
            # Unprocessable Entity
            print(error_detail[0]["msg"])
        elif response.status_code == 401:
            # Unauthorized
            if response.request.url.path == "/token":
                # Provided username-password credentials is incorrect.
                print(error_detail)
            else:
                print(
                    "Invalid API token provided." "Please use `lnkshrt login` to generate a token."
                )
        else:
            print(error_detail)
        raise typer.Exit(1)


def register_user(username: str, password: str, email: str) -> str:
    """Create user account."""
    res = _send_request(
        method="POST",
        endpoint="/signup",
        json={"username": username, "password": password, "email": email},
    )
    return res["message"]


def create_token(username: str, password: str) -> str:
    """Generates access token."""
    headers = {"accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
    res = _send_request(
        method="POST",
        endpoint="/token",
        data={"username": username, "password": password},
        headers=headers,
    )
    return res["access_token"]


def create_link(url: str, custom_path: str | None = None) -> str:
    """
    Create a shortened URL.

    Sends a request to the link shortening service API to generate a
    shortened URL based on the provided `url`. If a `custom_path` is specified,
    it will be used as the custom part of the shortened URL.
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}

    res = _send_request(
        method="POST",
        endpoint="/links",
        json={"url": url, "custom_path": custom_path},
        headers=headers,
    )

    return res["shortened_url"]


def delete_link(url: str) -> str:
    """
    Delete a shortened URL.

    Sends a request to the link shortening service API to delete the shortened link
    specified by the provided `url`. The `url` parameter should include the full URL
    of the shortened link, including the domain and path.
    """
    path = urlsplit(url).path

    headers = {"Authorization": f"Bearer {TOKEN}"}
    res = _send_request(
        method="DELETE",
        endpoint=f"/links{path}",
        headers=headers,
    )
    return res["message"]


def create_qr_code(text: str, destination: str) -> None:
    """
    Generate a QR code image from the provided text and save it to the specified destination.

    The file path should exist and also include the file name.
    """
    img = qrcode.make(text)
    img.save(destination)


def validate_url(url: str) -> bool:
    """Validates whether a given URL is valid and accessible."""
    scheme = urlsplit(url).scheme
    if scheme == "":
        print(
            "URL scheme is missing. Please include 'http://' or 'https://' "
            "at the beginning of the URL.   "
        )
        raise typer.Abort()
    elif scheme not in ALLOWED_SCHEMES:
        print("Invalid URL scheme. Only 'http://' and 'https://' schemes are allowed.")
        raise typer.Abort()

    res = _send_request(method="GET", base_url=url, endpoint="/ping")
    if res:
        return True
    return False
