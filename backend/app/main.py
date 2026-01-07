from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth, upload, predict
from app.core.logger import setup_logging

setup_logging()

app = FastAPI(title="Face Mask Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: allow all origin; production: chỉnh lại
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(predict.router, prefix="/predict", tags=["predict"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Face Mask Detection Backend"}
