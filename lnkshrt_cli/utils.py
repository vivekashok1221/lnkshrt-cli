import typing
from urllib.parse import urljoin, urlsplit

import httpx
import typer
from httpx import HTTPStatusError

from lnkshrt_cli.config import INSTANCE_URL, TOKEN


def _send_request(
    method: str,
    endpoint: str,
    json: dict[str, typing.Any] | None = None,
    data: dict[str, typing.Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, typing.Any]:
    with httpx.Client() as client:
        response = client.request(
            method=method,
            url=urljoin(INSTANCE_URL, endpoint),
            json=json,
            data=data,
            headers=headers,
        )
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
                    "Invalid API token provided."
                    "Please use `lnkshrt login` to generate a new token."
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

    return urljoin(INSTANCE_URL, res["shortened_url"])


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
