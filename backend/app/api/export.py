from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.session_service import SessionService

router = APIRouter(prefix="/export", tags=["Export"])

@router.get("/csv")
def export_csv(db: Session = Depends(get_db)):
    csv_data = SessionService.export_dataset_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=behavepass_dataset.csv"
        }
    )
