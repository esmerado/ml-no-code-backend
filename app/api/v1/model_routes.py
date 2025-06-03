from fastapi import HTTPException, File, UploadFile, APIRouter, Depends, Form

from app.services.model_service import ModelService
from app.utils.auth import verify_token

router = APIRouter()


# Para modelos de no mucho tamaño
@router.post("/models/train")
async def model_train(file: UploadFile = File(...),
                      target: str = Form(...),
                      user: dict = Depends(verify_token)):
    user_id = user.get("id")
    print("🔐 User ID:", user_id)

    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    service = ModelService(file=file, target=target, user_id=user_id)
    res_data = await service.train()
    if not res_data or not isinstance(res_data, list):
        raise HTTPException(status_code=500, detail="❌ No se pudo insertar el modelo.")

    model_entry = res_data[0]
    import json

    metrics = json.loads(model_entry["metrics_json"])

    return {
        "metrics": metrics,
        "model": model_entry,
        "predictions": [],  # TODO añadir predicciones
        "summary": f"Modelo {model_entry['model_name']} entrenado sobre {model_entry['target_column']}"
    }
