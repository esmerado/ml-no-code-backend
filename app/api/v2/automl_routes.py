# FastAPI pipeline: AutoML desde CSV hasta resultados (entrenamiento, predicción, métricas)

import os

import boto3
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from supabase import create_client

from app.services.automl_service import train_from_s3, predict_from_s3
from app.utils.auth import verify_token
from app.utils.supabase_utils import save_model_metadata

router = APIRouter()

# AWS Clients
BUCKET_NAME = "mindlessmldatasets"
FREEMIUM_BUCKET_NAME = "freemium"
BUCKET_OUTPUT_NAME = "s3://mindlessmloutputs/"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="eu-west-3"
)
lambda_client = boto3.client("lambda", region_name="eu-west-3")

sf = boto3.client('stepfunctions', region_name="eu-west-3")

# Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class TrainRequest(BaseModel):
    dataset_s3_path: str
    target_column: str
    output_model_s3_path: str


@router.post("/api/automl-train")
def train(req: TrainRequest,
          user: dict = Depends(verify_token)):
    user_id = user.get("id")
    user_type = user.get("user_type")

    try:

        model_id, metrics, df_test, model_output_path, data_output_path = train_from_s3(
            user_id,
            req.dataset_s3_path,
            req.target_column,
            f"{FREEMIUM_BUCKET_NAME}/{user_id}"
        )

        print("Llego a save model metadata", model_output_path, data_output_path)
        save_model_metadata(
            user_id,
            model_id,
            req.target_column,
            model_output_path,
            data_output_path,
            metrics
        )

        df_test_2 = df_test.replace([np.inf, -np.inf], np.nan).fillna(value="null")
        df_test_preview = df_test_2.head(5)

        return {
            "model_id": model_id,
            "metrics": metrics,
            "data": df_test_preview.to_dict(orient="records"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PredictRequest(BaseModel):
    model_s3_path: str
    input_data_s3_path: str


@router.post("/api/automl-predict")
def predict(req: PredictRequest):
    try:
        results = predict_from_s3(req.model_s3_path, req.input_data_s3_path)
        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
