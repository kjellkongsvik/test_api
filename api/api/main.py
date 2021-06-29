from fastapi import FastAPI, Security

from . import routes
from .auth import get_auth

app = FastAPI()

app.include_router(routes.router, dependencies=[Security(get_auth())])


@app.get("/health")
async def health():
    pass
