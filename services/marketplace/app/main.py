from pydantic import BaseModel, Field
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from .db import async_session, engine
from .models import Base, Capsule as CapsuleModel
from sqlalchemy import select

# Marketplace service removed – no FastAPI app
