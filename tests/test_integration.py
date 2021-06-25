import os
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ADDR = os.getenv("API_ADDR", "http://localhost:5000")
AUTHORITY = os.getenv("AUTHORITY", "http://localhost:8089/common")
CLIENT_ID = os.getenv("CLIENT_ID")


@pytest.fixture(scope="session")
def auth():
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    s.mount("http://", HTTPAdapter(max_retries=retries))
    r = s.get(f"{AUTHORITY}/.well-known/openid-configuration")
    assert r
    oidc = r.json()

    authorization_endpoint = oidc["authorization_endpoint"]

    r = requests.get(
        authorization_endpoint,
        f"client_id={CLIENT_ID}"
        "&response_type=code"
        "&redirect_uri=h"
        "&scope=openid"
        "&state=1234"
        "&nonce=5678"
        "&response_mode=fragment",
        allow_redirects=False,
    )
    assert r
    code = parse_qs(urlparse(r.headers["location"]).fragment)["code"][0]

    data = (
        "grant_type=authorization_code"
        + f"&client_id={CLIENT_ID}"
        + f"&code={code}"
        + "&redirect_uri=h"
    )
    headers = {"content-type": "application/x-www-form-urlencoded"}
    r = requests.post(
        oidc["token_endpoint"],
        str.encode(data),
        headers=headers,
    )
    assert r
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def healthy():
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1)
    s.mount("http://", HTTPAdapter(max_retries=retries))
    r = s.get(f"{API_ADDR}/health")
    assert r


def test_root_no_access(healthy):
    r = requests.get(API_ADDR)
    assert r.status_code == 403


def test_root(healthy, auth):
    r = requests.get(f"{API_ADDR}/", headers=auth)
    assert r
