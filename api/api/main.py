from fastapi import FastAPI, Security

from . import routes
from .auth import auth

app = FastAPI()

app.include_router(routes.router, dependencies=[Security(auth())])


@app.get("/health")
async def health():
    pass
