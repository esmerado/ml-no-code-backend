#!/usr/bin/env python3

# Init
# uvicorn main:app --reload

from app.api.v1 import model_routes
from fastapi import FastAPI

app = FastAPI()

app.include_router(model_routes.router, prefix="/api/v1")
