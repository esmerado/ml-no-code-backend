#!/usr/bin/env python3

# Init
# uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v2 import users_routes

app = FastAPI()

# client = OpenAI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_routes.router, prefix="/ml_backend/v2")
# app.include_router(aws_routes.router, prefix="/ml_backend/v2")
# app.include_router(models_routes.router, prefix="/ml_backend/v2")
# app.include_router(automl_routes.router, prefix="/ml_backend/v2")
