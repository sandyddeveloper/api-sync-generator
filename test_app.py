from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import datetime

app = FastAPI(title="api-sync-test", version="1.0.0")

class User(BaseModel):
    id: int
    username: str
    is_active: bool = True
    created_at: datetime.datetime

class CreateUserReq(BaseModel):
    username: str
    password: str

@app.get("/users", response_model=List[User], tags=["users"])
def get_users(active_only: bool = False):
    """Get all users"""
    pass

@app.post("/users", response_model=User, tags=["users"])
def create_user(req: CreateUserReq):
    """Create a user"""
    pass

@app.get("/internal/stats", response_model=dict, tags=["@internal"])
def internal_stats():
    """This should be ignored by the generator."""
    pass
