# main.py

import os

from dotenv import load_dotenv
from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel
from supabase import create_client

from app.utils.auth import sync_verify_token, verify_token
from app.utils.supabase_utils import get_user_consents

load_dotenv()

router = APIRouter()

# Supabase config
SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/sync")
async def sync_user(user: dict = Depends(sync_verify_token)):
    user_id = user.get("id")
    email = user.get("email")
    existing = supabase.table("users").select("*").eq("id", user_id).execute()

    if existing.data:
        return {
            "message": "Usuario ya sincronizado",
            "user_id": existing.data[0]["id"],
            "user_type": existing.data[0]["user_type"]
        }

    res = supabase.table("users").insert({"id": user_id, "email": email, "terms": True, "cookies": True}).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to register user")

    return {
        "message": "Usuario registrado",
        "user_id": res.data[0]["id"],
        "user_type": res.data[0]["user_type"]
    }


class CookieConsentUpdate(BaseModel):
    cookies: bool
    terms: bool


@router.post("/consent")
async def update_consent(
        payload: CookieConsentUpdate,
        user: dict = Depends(verify_token)
):
    user_id = user.get("id")
    update_data = {
        "cookies": payload.cookies,
        "terms": payload.terms
    }

    response = supabase.table("users").update(update_data).eq("id", user_id).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Error al actualizar consentimiento")

    return {"message": "Consentimiento actualizado"}


class AddToWaitlistRequest(BaseModel):
    email: str
    suggestions: str = None


@router.post("/waitlist")
def add_to_waitlist(request: AddToWaitlistRequest):
    email = request.email
    suggestions = request.suggestions
    print("Adding to waitlist:", email, suggestions)
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    existing = supabase.table("emails").select("*").eq("email", email).execute()

    if existing.data:
        return {"message": "Email already in waitlist"}

    res = supabase.table("emails").insert({"email": email, "suggestions": suggestions}).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to add to waitlist")

    return {"message": "Email added to waitlist"}


class FeedbackRequest(BaseModel):
    message: str = None


@router.post("/feedback")
def user_feedback(request: FeedbackRequest, user: dict = Depends(sync_verify_token)):
    message = request.message
    user_id = user.get("id")

    res = supabase.table("feedback").insert({"user_id": user_id, "message": message}).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to add to feeback")

    return {"message": "Feedback added successfully"}


class EnterpriseFormRequest(BaseModel):
    email: str = None
    message: str = None
    name: str = None


@router.post("/form-enterprise")
def user_feedback(request: EnterpriseFormRequest):
    message = request.message
    email = request.email
    name = request.name

    res = supabase.table("formulario_empresas").insert({
        "email": email,
        "message": message,
        "name": name
    }).execute()

    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to add to form information")

    return {"message": "Form information added successfully"}


@router.get("/consents")
def get_models(user: dict = Depends(verify_token)):
    user_id = user.get("id")

    try:
        data = get_user_consents(user_id)
        print(f"Fetched models for user {user_id}: {data}")
        return {"terms": data.get("terms", False), "cookies": data.get("cookies", False)}
    except Exception as e:
        print(f"Error fetching models for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
