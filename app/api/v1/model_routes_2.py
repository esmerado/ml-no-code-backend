import os
import tempfile
import traceback

import pandas as pd
from fastapi import File, UploadFile, APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from pycaret.regression import setup, compare_models, predict_model, pull

from app.models.deepseek_client import DeepSeekClient
from app.schemas.model_schema import TrainResponse
from app.utils.auth import verify_token

router = APIRouter()


@router.get("/upload-dataset/{user_id}", response_model=TrainResponse)
def upload_dataset(user_id: int):
    """
    Endpoint to upload a dataset for training.
    """
    # Here you would typically handle the file upload and save it to a location
    # For now, we will just return a success message
    return {"message": "Dataset uploaded successfully", "user_id": user_id}


def build_model_prompt(model: str, metrics: list, predictions: list) -> str:
    metric = metrics[0] if metrics else {}

    # Extrae las predicciones como strings de números
    preds = [p.get("price", "N/A") for p in predictions[:5]]
    pred_str = ", ".join(str(p) for p in preds)

    # Construye un prompt con texto plano (sin estructuras tipo dict)
    prompt = (
        f"Eres un asistente experto en machine learning. "
        f"Resume los resultados del siguiente modelo de forma clara y sencilla para un usuario sin conocimientos técnicos.\n\n"
        f"🔹 Modelo: {model}\n"
        f"🔸 MAE: {metric.get('MAE', 'N/A')}\n"
        f"🔸 RMSE: {metric.get('RMSE', 'N/A')}\n"
        f"🔸 R2: {metric.get('R2', 'N/A')}\n"
        f"🔸 MAPE: {metric.get('MAPE', 'N/A')}\n\n"
        f"Predicciones ejemplo: {pred_str}\n\n"
        f"Explica si el modelo es bueno, qué significan esas métricas y para qué podría servir este modelo."
    )

    return prompt


@router.post("/train-model/csv/{correlationId}", response_model=TrainResponse)
async def train_model_csv(
        correlationId: int,
        file: UploadFile = File(...),
        target: str = Form(...),
        user: dict = Depends(verify_token)
):
    try:
        print(f"🔐 Usuario autenticado: {user.get('email')}")
        print(f"📁 Archivo recibido: {file.filename}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        print(f"📌 CSV temporal guardado en: {tmp_path}")
        df = pd.read_csv(tmp_path)

        print(f"📊 DataFrame con forma: {df.shape}")
        if target not in df.columns:
            return JSONResponse(status_code=400, content={"error": f"La columna '{target}' no existe en el archivo."})

        print(f"🎯 Columna objetivo: {target}")
        setup(data=df, target=target, verbose=False, session_id=123)
        print("✅ PyCaret setup hecho.")

        best_model = compare_models()
        predictions = predict_model(best_model, data=df)
        results = pull()

        os.remove(tmp_path)

        columns_to_return = [col for col in ['Label', target] if col in predictions.columns]
        prediction_sample = predictions[columns_to_return].head(10).to_dict(orient="records")

        model_results = {
            "model": str(best_model),
            "metrics": results.to_dict(orient="records"),
            "predictions": prediction_sample
        }

        prompt = build_model_prompt(
            model=model_results["model"],
            metrics=model_results["metrics"],
            predictions=model_results["predictions"]
        )
        prompt_result = DeepSeekClient().get_response(prompt)

        model_results["summary"] = prompt_result

        return model_results

    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
