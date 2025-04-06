from typing import List, Dict

from pydantic import BaseModel


class FeatureImportance(BaseModel):
    features: List[str]
    values: List[float]


class TrainResponse(BaseModel):
    metrics: List[Dict]
    model: str
    predictions: List[Dict]
    summary: str
