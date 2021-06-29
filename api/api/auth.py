import os
from functools import lru_cache

import requests
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

AUTHORITY = os.getenv("AUTHORITY")
AUDIENCE = os.getenv("AUDIENCE")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

assert AUTHORITY is not None
assert AUDIENCE is not None


class Oauth(HTTPBearer):
    def __init__(self, authority, audience):
        super().__init__()

        s = requests.Session()
        retries = Retry(total=5, backoff_factor=1)
        s.mount("http://", HTTPAdapter(max_retries=retries))
        config = s.get(f"{authority}/.well-known/openid-configuration").json()

        self.audience = audience
        self.public_keys = requests.get(config.get("jwks_uri")).json()
        self.issuer = config.get("issuer")
        self.token_endpoint = config.get("token_endpoint")
        self.id_token_signing_alg_values_supported = config.get(
            "id_token_signing_alg_values_supported"
        )

    async def __call__(self, request: Request):
        token = (await super().__call__(request)).credentials
        try:
            jwt.decode(
                token,
                self.public_keys,
                algorithms=self.id_token_signing_alg_values_supported,
                audience=self.audience,
                issuer=self.issuer,
            )
        except JWTError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    async def obo(self, token, scope):
        data = (
            "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer"
            + f"&client_id={CLIENT_ID}"
            + f"&client_secret={CLIENT_SECRET}"
            + f"&assertion={token}"
            + f"&scope={scope}"
            + "&requested_token_use=on_behalf_of"
        )
        headers = {"content-type": "application/x-www-form-urlencoded"}
        r = requests.post(
            self.token_endpoint,
            str.encode(data),
            headers=headers,
        )
        if not r:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return r.json().get("access_token")


@lru_cache
def get_auth():
    authority = os.getenv("AUTHORITY")
    audience = os.getenv("AUDIENCE")

    assert authority is not None
    assert audience is not None

    return Oauth(authority, audience)
