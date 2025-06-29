import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def save_model_metadata(user_id, model_id, target_column, s3_path, data_s3_path, metrics, name, task_type):
    data = {
        "name": name,
        "user_id": user_id,
        "model_id": model_id,
        "target_column": target_column,
        "model_s3_path": s3_path,
        "model_s3_data_path": data_s3_path,
        "model_type": task_type,
    }
    if task_type == "classification":
        data.update({
            "accuracy": metrics.get("accuracy"),
            "f1_score": metrics.get("f1_score"),
            "precision": metrics.get("precision"),
            "recall": metrics.get("recall"),
        })
    else:
        data.update({
            "rmse": metrics.get("mse"),
            "mae": metrics.get("mae"),
            "r2": metrics.get("r2"),
        })

    supabase.table("models").insert(data).execute()


def get_user_data(user_id: str):
    user = supabase.table("users").select("*").eq("id", user_id).execute()

    return user.data[0] if user.data else None


def get_user_data_by_email(user_email: str):
    user = supabase.table("users").select("*").eq("email", user_email).execute()

    return user.data[0] if user.data else None


def get_user_consents(user_id: str):
    user = supabase.table("users").select("cookies, terms").eq("id", user_id).execute()

    return user.data[0] if user.data else None


def get_user_models(user_id: str):
    models = supabase.table("models").select("*").eq("user_id", user_id).execute()

    return models.data if models.data else []


def get_user_models_number(user_id: str):
    models = supabase.table("models").select("model_id").eq("user_id", user_id).execute()

    return len(models.data) if models.data else 0


def get_model(model_id: str):
    model = supabase.table("models").select("*").eq("model_id", model_id).execute()

    return model.data[0] if model.data else None


def set_predictions_summary(model_id: str, s3_key: str):
    data = {
        "summary_path": s3_key
    }

    supabase.table("predictions").update(data).eq("model_id", model_id).execute()


def get_predictions(model_id: str):
    model = supabase.table("predictions").select("*").eq("model_id", model_id).execute()

    return model.data[0] if model.data else None


def save_model_prediction(model_id: str, prediction_path: str):
    data = {
        "model_id": model_id,
        "prediction_path": prediction_path
    }

    supabase.table("predictions").insert(data).execute()
