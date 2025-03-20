from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import AfterValidator, BaseModel
from sqlmodel import SQLModel, select

from yapml.datamodel import BoundingBox, Label, ObjectDetectionSample, is_valid_hex_color, is_valid_label_name
from yapml.db import engine, get_session
from yapml.fixtures import populate_db

router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_session)])
