from fastapi import APIRouter

from app.schemas.model_schema import TrainResponse, FeatureImportance
from app.services.model_service import RandomForestTrainer

router = APIRouter()


@router.get("/train/randomforest", response_model=TrainResponse)
def train_rf():
    trainer = RandomForestTrainer()
    result = trainer.train()

    response = TrainResponse(
        accuracy=result["accuracy"],
        confusion_matrix=result["confusion_matrix"],
        feature_importance=FeatureImportance(
            features=result["feature_importance"]["features"],
            values=result["feature_importance"]["values"]
        ),
        target_names=result["target_names"],
        epochs=result["epochs"],
        accuracy_values=result["accuracy_values"],
        loss_values=result["loss_values"]
    )
    return response
