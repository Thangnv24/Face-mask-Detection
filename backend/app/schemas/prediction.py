from pydantic import BaseModel

class PredictionResult(BaseModel):
    mask: bool
    confidence: float
