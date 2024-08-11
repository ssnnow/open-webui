import io
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
    Request,
    UploadFile,
    File,
    Form,
)


from datetime import datetime, timedelta
from typing import List, Union, Optional
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse

from pydantic import BaseModel
import uuid
import logging
from apps.webui.models.files import (
    Files,
    FileForm,
    FileModel,
    FileModelResponse,
)
from apps.storage.provider import StorageProvider
from utils.utils import get_verified_user, get_admin_user
from constants import ERROR_MESSAGES

log = logging.getLogger(__name__)
router = APIRouter()
storage = StorageProvider()

############################
# Upload File
############################

@router.post("/")
async def upload_file(file: UploadFile = File(...), user=Depends(get_verified_user)):
    try:
        id = str(uuid.uuid4())
        dst_filename = f"{user.id}/{id}_{file.filename}"
        storage.upload_file(file.file, dst_filename)
        result = Files.insert_new_file(
            user.id,
            FileForm(
                **{
                    "id": id,
                    "filename": f"{id}_{file.filename}",
                    "meta": {
                        "name": f"{id}_{file.filename}",
                        "content_type": file.content_type,
                        "size": file.size,
                        "path": user.id,
                    },
                }
            ),
        )
        if result:
                    return result
        else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ERROR_MESSAGES.DEFAULT("Error uploading file"),
                    )
    except RuntimeError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error uploading file to storage"),
        )

############################
# List Files
############################

@router.get("/", response_model=List[BaseModel])
async def list_files(user=Depends(get_verified_user)):
    try:
        files = storage.list_files()
        return files
    except RuntimeError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error listing files in storage"),
        )

############################
# Delete All Files
############################

@router.delete("/all")
async def delete_all_files(user=Depends(get_admin_user)):
    try:
        storage.delete_all_files()
        return {"message": "All files deleted successfully"}
    except RuntimeError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT("Error deleting files from storage"),
        )

############################
# Get File By Id
############################

@router.get("/{id}", response_model=Optional[BaseModel])
async def get_file_by_id(id: str, user=Depends(get_verified_user)):
    try:
        file = storage.get_file(id)
    except (FileNotFoundError, RuntimeError) as e:
        log.exception(e)
        if '404' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error fetching file from storage"),
            )
    return file
############################
# Get File Content By Id
############################

@router.get("/{id}/content")
async def get_file_content_by_id(id: str, user=Depends(get_verified_user)):
    filename = f"{id}_{id}"
    try:
        file_content, content_type = storage.get_file(filename)
        return StreamingResponse(io.BytesIO(file_content), media_type=content_type)
    except (FileNotFoundError, RuntimeError) as e:
        log.exception(e)
        if '404' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error fetching file content from storage"),
            )

############################
# Delete File By Id
############################

@router.delete("/{id}")
async def delete_file_by_id(id: str, user=Depends(get_verified_user)):
    filename = f"{id}_{id}"
    try:
        storage.delete_file(filename)
        return {"message": "File deleted successfully"}
    except (FileNotFoundError, RuntimeError) as e:
        log.exception(e)
        if '404' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.NOT_FOUND,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting file from storage"),
            )
