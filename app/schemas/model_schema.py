from typing import List

from pydantic import BaseModel


class FeatureImportance(BaseModel):
    features: List[str]
    values: List[float]


class TrainResponse(BaseModel):
    accuracy: float
    confusion_matrix: List[List[int]]
    feature_importance: FeatureImportance
    target_names: List[str]
    epochs: int
    accuracy_values: List[float]
    loss_values: List[float]
