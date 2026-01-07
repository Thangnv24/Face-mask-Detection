from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from app.core.security import get_current_user
from app.services.minio_service import minio_client, upload_fileobj, settings as minio_settings
import uuid

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...), user=Depends(get_current_user)):
    # generate unique name
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    object_name = f"{uuid.uuid4().hex}.{ext}"
    try:
        # file.file is a SpooledTemporaryFile; we can pass to minio client
        upload_fileobj(minio_settings.MINIO_BUCKET, object_name, file.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"object_name": object_name}
