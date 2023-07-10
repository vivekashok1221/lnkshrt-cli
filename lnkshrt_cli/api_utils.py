import httpx

url = "0.0.0.0:8000"


def register_user(username: str, password: str, email: str):
    res = httpx.post(url=url, json={"username": username, "password": password, "email": email})
    if res.status_code == 200:
        return res.json()["message"]
    else:
        return res.json()["detail"]
