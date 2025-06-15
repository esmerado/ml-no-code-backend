from fastapi import FastAPI, HTTPException, Depends, APIRouter

from app.utils.auth import verify_token
from app.utils.supabase_utils import get_user_models

app = FastAPI()
router = APIRouter()


# DEPRECATED: This code is for an older version of the API.

@router.get("/api/user/get-models")
def get_models(user: dict = Depends(verify_token)):
    user_id = user.get("id")

    try:
        models = get_user_models(user_id)
        print(f"Fetched models for user {user_id}: {models}")
        return {"models": models}
    except Exception as e:
        print(f"Error fetching models for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
