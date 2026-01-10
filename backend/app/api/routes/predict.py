from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional
from app.core.security import get_current_user
from app.services import ai_service, minio_service

router = APIRouter()

class PredictIn(BaseModel):
    object_name: str

@router.post("/from-minio")
def predict_from_minio(payload: PredictIn, user=Depends(get_current_user)):
    object_name = payload.object_name
    try:
        local_path = minio_service.download_to_temp(minio_service.settings.MINIO_BUCKET, object_name)
        result = ai_service.predict_mask(local_path)
        return {"object_name": object_name, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/from-file")
def predict_from_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    user=Depends(get_current_user)
):
    """
    Predict from uploaded file.
    
    Args:
        file: Uploaded image file
        session_id: Optional session ID for tracking (enables BoT-SORT)
        user: Authenticated user
        
    Returns:
        Detection results with drawn image
    """
    tmp_path = ai_service.save_upload_file_tmp(file)
    
    if session_id:
        # Use tracking-enabled detection
        result = ai_service.predict_from_image_path_with_tracking(tmp_path, session_id, draw_on_image=True)
    else:
        # Use stateless detection
        result = ai_service.predict_from_image_path(tmp_path, draw_on_image=True)
    
    return result

@router.post("/from-file-json")
def predict_from_file_json(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    user=Depends(get_current_user)
):
    """
    Predict from uploaded file, return JSON only (no image).
    
    Args:
        file: Uploaded image file
        session_id: Optional session ID for tracking (enables BoT-SORT)
        user: Authenticated user
        
    Returns:
        Detection results as JSON
    """
    tmp_path = ai_service.save_upload_file_tmp(file)
    
    if session_id:
        # Use tracking-enabled detection
        result = ai_service.predict_from_image_path_with_tracking(tmp_path, session_id, draw_on_image=False)
    else:
        # Use stateless detection
        result = ai_service.predict_from_image_path(tmp_path, draw_on_image=False)
    
    return result
