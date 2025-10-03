"""
Report viewing API endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.report_parameter import (
    ReportViewRequest,
    ReportDataResponse,
    ReportParameterResponse,
    ReportParameterCreate,
    ReportParameterUpdate
)
from app.services.report_view_service import ReportViewService
from app.models.report_parameter import ReportParameter

router = APIRouter()


@router.post("/execute", response_model=ReportDataResponse)
def execute_report(
    request: ReportViewRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a report with given parameters and return the data
    """
    try:
        service = ReportViewService(db)
        result = service.execute_report(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report execution failed: {str(e)}")


@router.get("/{report_id}/parameters", response_model=List[ReportParameterResponse])
def get_report_parameters(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all parameters for a report
    """
    try:
        service = ReportViewService(db)
        parameters = service.get_report_parameters(report_id)
        return parameters
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{report_id}/parameters", response_model=ReportParameterResponse)
def create_report_parameter(
    report_id: str,
    parameter: ReportParameterCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new parameter for a report
    """
    try:
        # Ensure report_id matches
        parameter.report_id = report_id

        db_parameter = ReportParameter(**parameter.dict())
        db.add(db_parameter)
        db.commit()
        db.refresh(db_parameter)
        return db_parameter
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/parameters/{parameter_id}", response_model=ReportParameterResponse)
def update_report_parameter(
    parameter_id: str,
    parameter_update: ReportParameterUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a report parameter
    """
    try:
        db_parameter = db.query(ReportParameter).filter(ReportParameter.id == parameter_id).first()
        if not db_parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")

        # Update fields
        update_data = parameter_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_parameter, field, value)

        db.commit()
        db.refresh(db_parameter)
        return db_parameter
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/parameters/{parameter_id}")
def delete_report_parameter(
    parameter_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a report parameter
    """
    try:
        db_parameter = db.query(ReportParameter).filter(ReportParameter.id == parameter_id).first()
        if not db_parameter:
            raise HTTPException(status_code=404, detail="Parameter not found")

        db.delete(db_parameter)
        db.commit()
        return {"message": "Parameter deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))