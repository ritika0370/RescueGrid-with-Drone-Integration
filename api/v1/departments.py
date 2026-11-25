"""
Emergency Department Registry API.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_admin
from app.models.department import Department
from app.models.incident import Incident
from app.schemas.department import DepartmentCreateRequest, DepartmentResponse
from app.schemas.incident import IncidentResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=List[DepartmentResponse])
async def list_departments(db: AsyncSession = Depends(get_db)):
    """List all registered emergency departments."""
    res = await db.execute(select(Department).order_by(Department.name.asc()))
    return res.scalars().all()


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    req: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """Register a new emergency department (Fire, Police, Disaster, Medical)."""
    dept = Department(
        name=req.name,
        department_type=req.department_type,
        service_area=req.service_area,
        latitude=req.latitude,
        longitude=req.longitude,
        contact_information=req.contact_information,
        status=req.status,
        supported_categories=req.supported_categories,
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific department."""
    res = await db.execute(select(Department).where(Department.id == department_id))
    dept = res.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")
    return dept


@router.get("/{department_id}/incidents", response_model=List[IncidentResponse])
async def get_department_incidents(department_id: str, db: AsyncSession = Depends(get_db)):
    """List all incidents assigned to a department."""
    res = await db.execute(
        select(Incident).where(Incident.assigned_department_id == department_id).order_by(Incident.priority.asc())
    )
    return res.scalars().all()
