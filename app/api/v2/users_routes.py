# main.py

import os

from dotenv import load_dotenv
from fastapi import HTTPException, Depends, APIRouter
from supabase import create_client

from app.utils.auth import verify_token

load_dotenv()

router = APIRouter()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/sync")
async def sync_user(user: dict = Depends(verify_token)):
    user_id = user.get("id")
    email = user.get("email")
    existing = supabase.table("users").select("*").eq("email", email).execute()

    if existing.data:
        return {
            "message": "Usuario ya sincronizado",
            "user_id": existing.data[0]["id"],
            "user_type": existing.data[0]["user_type"]
        }

    print("🔐 User", user)
    res = supabase.table("users").insert({"id": user_id, "email": email}).execute()

    print("res", res)
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to register user")

    return {
        "message": "Usuario registrado",
        "user_id": res.data[0]["id"],
        "user_type": res.data[0]["user_type"]
    }
