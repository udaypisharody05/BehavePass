from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.session import (
    CreateSessionPayload, SessionResponse, SessionSummaryResponse
)
from app.services.feature_validator import FeatureValidator
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: CreateSessionPayload, db: Session = Depends(get_db)):
    # 1. Validate for forbidden keys or non-finite values
    valid, msg = FeatureValidator.validate_payload(payload.model_dump())
    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # 2. Store session
    try:
        session_obj = SessionService.create_session(db, payload)
        return session_obj
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("", response_model=List[SessionSummaryResponse])
def list_sessions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return SessionService.list_session_summaries(db, skip=skip, limit=limit)

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)):
    session_obj = SessionService.get_session_by_id(db, session_id)
    if not session_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session_obj

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    deleted = SessionService.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return None
