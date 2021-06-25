import os
from functools import lru_cache
import requests
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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


@lru_cache
def auth():
    AUTHORITY = os.getenv("AUTHORITY")
    AUDIENCE = os.getenv("AUDIENCE")

    assert AUTHORITY is not None
    assert AUDIENCE is not None

    return Oauth(AUTHORITY, AUDIENCE)
