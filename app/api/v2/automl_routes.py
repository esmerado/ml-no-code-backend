# FastAPI pipeline: AutoML desde CSV hasta resultados (entrenamiento, predicción, métricas)

import json
import os

import boto3
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from supabase import create_client

from app.api.v2.deepseek_routes import summarize_predictions, PredictionResults
from app.services.automl_service import train_from_s3, predict_from_s3
from app.utils.auth import verify_token
from app.utils.s3_utils import download_file_from_s3
from app.utils.supabase_utils import save_model_metadata, get_model, get_predictions

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
    model_id: str
    model_name: str
    dataset_s3_path: str
    target_column: str


@router.post("/api/automl-train")
def train(req: TrainRequest,
          user: dict = Depends(verify_token)):
    user_id = user.get("id")
    user_type = user.get("user_type")

    try:

        model_id, task_type, metrics, df_test, model_output_path, data_output_path = train_from_s3(
            user_id,
            req.model_id,
            req.dataset_s3_path,
            req.target_column,
            f"{FREEMIUM_BUCKET_NAME}/{user_id}"
        )

        save_model_metadata(
            user_id,
            model_id,
            req.target_column,
            model_output_path,
            data_output_path,
            metrics,
            req.model_name,
            task_type
        )

        df_test_2 = df_test.replace([np.inf, -np.inf], np.nan).fillna(value="null")
        df_test_preview = df_test_2.head(5)

        # Not neccessary to return all this info
        return {
            "model_id": model_id,
            "metrics": metrics,
            "data": df_test_preview.to_dict(orient="records"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PredictInput(BaseModel):
    s3_dataset_path: str


@router.post("/api/automl-predict/{model_id}")
async def predict(model_id: str, payload: PredictInput, user: dict = Depends(verify_token)):
    try:
        user_id = user.get("id")
        model_data = get_model(model_id)

        if not model_data:
            raise HTTPException(status_code=404, detail="Model not found")

        model_s3_path = model_data.get("model_s3_path")
        s3_dataset_path = f"freemium/{user_id}/{payload.s3_dataset_path}"

        results = predict_from_s3(model_id, model_s3_path, s3_dataset_path)

        payload = PredictionResults(data=results)
        summary_res = await summarize_predictions(model_id, payload, user)
        return {"predictions": results, "summary": summary_res.get("summary")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GetModelDataRequest(BaseModel):
    model_id: str


@router.get("/api/get-model/{model_id}")
def get_model_info(model_id: str, user: dict = Depends(verify_token)):
    try:
        model_data = get_model(model_id)
        if not model_data:
            raise HTTPException(status_code=404, detail="Model not found")

        s3_key = model_data.get("model_s3_data_path")
        local_path = f"/tmp/{model_id}_data.csv"
        download_file_from_s3(s3_key, local_path)

        table_df = pd.read_csv(local_path)
        table_data = json.loads(table_df.to_json(orient="records"))

        return {"model_data": model_data, "table_data": table_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/get-model-predictions/{model_id}")
def get_model_info(model_id: str, user: dict = Depends(verify_token)):
    try:
        predictions = get_predictions(model_id)
        if not predictions:
            raise HTTPException(status_code=404, detail="Model not found")

        s3_key = predictions.get("prediction_path")
        local_path = f"/tmp/{model_id}_data.csv"
        download_file_from_s3(s3_key, local_path)

        table_df = pd.read_csv(local_path)
        table_predictions = json.loads(table_df.to_json(orient="records"))

        summary_text = ""
        summary_s3_key = predictions.get("summary_path")

        if summary_s3_key:
            summary_local_path = f"/tmp/{model_id}_summary.md"
            download_file_from_s3(summary_s3_key, summary_local_path)

            try:
                with open(summary_local_path, "r", encoding="utf-8") as f:
                    summary_text = f.read()
            except Exception:
                summary_text = ""

        return {
            "predictions": table_predictions,
            "summary": summary_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/remove-model/{model_id}")
def get_model_info(model_id: str, user: dict = Depends(verify_token)):
    try:
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        supabase.table("predictions").delete().eq("model_id", model_id).execute()

        supabase.table("models").delete().eq("model_id", model_id).execute()

        s3_key = f"{FREEMIUM_BUCKET_NAME}/{user_id}/{model_id}.pkl"
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key)

        data_s3_key = f"{FREEMIUM_BUCKET_NAME}/{user_id}/df_test_{model_id}.csv"
        s3.delete_object(Bucket=BUCKET_NAME, Key=data_s3_key)

        data_s3_key = f"{FREEMIUM_BUCKET_NAME}/{user_id}/{model_id}_summary.md"
        s3.delete_object(Bucket=BUCKET_NAME, Key=data_s3_key)

        return {"message": "Model deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
