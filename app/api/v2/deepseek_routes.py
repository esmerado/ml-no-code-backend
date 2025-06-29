from typing import List, Dict, Any

import unicodedata
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.utils.auth import verify_token
from app.utils.deepseek_utils import send_to_deepseek, build_prompt
from app.utils.s3_utils import upload_file_to_s3
from app.utils.supabase_utils import set_predictions_summary

router = APIRouter()


def convert_to_markdown(text: str) -> str:
    return unicodedata.normalize("NFC", text)


class PredictionResults(BaseModel):
    data: List[Dict[str, Any]]


@router.post("/summarize-predictions/{model_id}")
async def summarize_predictions(model_id: str, payload: PredictionResults, user: dict = Depends(verify_token)):
    user_id = user.get("id")

    if not payload.data:
        raise HTTPException(status_code=400, detail="No data provided.")

    max_items = 30
    trimmed_data = payload.data[:max_items]
    prompt = build_prompt(trimmed_data)

    summary = await send_to_deepseek(prompt)

    summary_md = convert_to_markdown(summary)

    filename = f"{model_id}_summary.md"
    folder = f"freemium/{user_id}"

    try:
        s3_key = upload_file_to_s3(
            file_bytes=summary_md.encode('utf-8'),
            filename=filename,
            folder=folder
        )

        set_predictions_summary(model_id, s3_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading summary to S3: {e}")

    return {"summary": summary_md}
