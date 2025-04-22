import os
import tempfile
import uuid

from fastapi import APIRouter, File, UploadFile, Depends
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client

from app.utils.auth import verify_token
from app.utils.s3_upload import upload_file_to_supabase

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/user/sync")
async def sync_user(request: Request):
    body = await request.json()
    user_id = body.get("id")
    email = body.get("email")
    name = body.get("name")

    if not user_id or not email:
        raise HTTPException(status_code=400, detail="ID y email son requeridos")

    # Verifica si ya existe en tu tabla
    existing = supabase.table("users").select("*").eq("id", user_id).execute()
    if existing.data:
        return {"message": "El usuario ya existe"}

    # Guarda en tu tabla
    res = supabase.table("users").insert({
        "id": user_id,
        "email": email,
        "name": name or "Sin nombre"
    }).execute()

    return {"message": "Usuario guardado", "user": res.data}


@router.get("/dataset/upload")
async def upload_file(file: UploadFile = File(...), user: dict = Depends(verify_token)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        print("FILE:", tmp)
        file_url = upload_file_to_supabase(tmp_path, user.get("sub"))

        print("usuario", user.get("sub"), user.get("id"))
        user_id = user.get("sub") or user.get("id")
        if file_url:
            existing = supabase.table("datasets").select("*").eq("file_url", file_url).execute()

            if existing.data:
                return {"message": "Un dataset con esta url ya existe"}
            res = supabase.table("datasets").insert({
                "id": uuid.uuid4(),
                "user_id": user_id,
                "filename": tmp.filename,
                "file_url": file_url,
                "file_type": file.content_type,
            }).execute()

        os.remove(tmp_path)
        return {"message": "Archivo subido correctamente", "url": file_url}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/models")
async def get_models():
    try:
        response = supabase.table("models").select("*").execute()

        if response.data is None:
            raise HTTPException(status_code=404, detail="No hay modelos")

        return {
            "message": "✅ Modelos encontrados",
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error con Supabase: {str(e)}")
