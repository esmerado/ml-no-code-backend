from fastapi import FastAPI, HTTPException, Depends, APIRouter
from pydantic import BaseModel
from sagemaker import Session
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput

from app.utils.auth import verify_token

app = FastAPI()
router = APIRouter()


class TrainRequest(BaseModel):
    dataset_s3_path: str
    target_column: str
    output_s3_path: str


@router.post("/api/train-xgb")
def train_xgb(request: TrainRequest):
    try:
        sagemaker_session = Session()
        role = 'arn:aws:iam::517681924045:user/Admin'
        xgb_image = '683313688378.dkr.ecr.eu-west-3.amazonaws.com/sagemaker-xgboost:1.7-1'

        estimator = Estimator(
            image_uri=xgb_image,
            role=role,
            instance_count=1,
            instance_type='ml.m5.large',
            volume_size=5,
            max_run=1800,
            output_path=request.output_s3_path,
            sagemaker_session=sagemaker_session,
            hyperparameters={"objective": "reg:squarederror", "num_round": "50"},
            environment={"TARGET_COLUMN": request.target_column}
        )

        estimator.fit({'train': TrainingInput(request.dataset_s3_path, content_type='text/csv')})

        return {"message": "Training started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/models/{model_id}/results")
def get_model_results(model_id: str,
                      user: dict = Depends(verify_token)):
    try:
        mock = {
            "model_id": model_id,
            "status": "COMPLETED",
            # "dataset": {
            #     "s3_input_path": request.dataset_s3_path,
            #     "s3_output_path": request.output_s3_path
            # },
            # "target_column": request.target_column,
            "evaluation": {
                "r2": 0.812,
                "rmse": 5.23,
                "mae": 3.84,
                "metrics_chart_url": "https://your-s3-or-app-url.com/metrics/r2-rmse-mae.png"
            },
            "predictions": [
                {
                    "id": "row_001",
                    "features": {
                        "location": "Madrid",
                        "size_m2": 70,
                        "rooms": 3
                    },
                    "real_price": 190.4,
                    "predicted_price": 187.4,
                    "confidence_interval": [180.2, 194.5]
                },
                {
                    "id": "row_002",
                    "features": {
                        "location": "Barcelona",
                        "size_m2": 85,
                        "rooms": 4
                    },
                    "real_price": 218.9,
                    "predicted_price": 215.9,
                    "confidence_interval": [209.0, 222.1]
                }
            ],
            "sagemaker_metadata": {
                "training_job_name": "xgb-train-2025-05-26-1730",
                "instance_type": "ml.t3.medium",
                "duration_seconds": 118,
                "created_at": "2025-05-26T17:30:00Z",
                "endpoint_url": "https://runtime.sagemaker.eu-west-3.amazonaws.com/endpoint/xgb-reg-2025-05-26-1730"
            }
        }

        return mock
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
