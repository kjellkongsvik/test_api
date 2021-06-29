import os

from azure.core.credentials import AccessToken
from azure.storage.blob import BlobServiceClient
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import get_auth

router = APIRouter()

STORAGE_URL = os.getenv("STORAGE_URL")
CONTAINER = "something"

class CustomTokenCredential(object):
    def __init__(self, token: str):
        self.__token = token

    def get_token(self, *scopes, **kwargs):
        return AccessToken(self.__token, 1)


@router.get("/", status_code=200)
async def index():
    pass


@router.post("/", status_code=201)
async def upload_file(
    auth_cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    auth=Depends(get_auth),
    file: UploadFile = File(...),
):
    token = await auth.obo(
        auth_cred.credentials, scope="https://storage.azure.com/user_impersonation"
    )
    credential = CustomTokenCredential(token)
    blob_service_client = BlobServiceClient(STORAGE_URL, credential)

    cc = blob_service_client.get_container_client(CONTAINER)
    if not cc.exists():
        cc.create_container()

    blob_client = cc.get_blob_client(blob=file.filename)
    if blob_client.exists():
        # TODO rather return some error code, but complicates setup
        blob_client.delete_blob()
    blob_client.upload_blob(await file.read())
