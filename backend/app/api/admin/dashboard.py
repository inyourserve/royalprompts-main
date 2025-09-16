"""
Admin Panel Dashboard Endpoints
Handles dashboard statistics and overview
"""
from fastapi import APIRouter, Depends

from app.core.admin_auth import get_current_admin
from app.schemas.admin import DashboardStats
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("", tags=["Admin Dashboard"])
async def get_dashboard(current_admin = Depends(get_current_admin)):
    """Simple dashboard with essential stats only"""
    admin_service = AdminService()
    stats = await admin_service.get_dashboard_stats()
    return DashboardStats(**stats)


@router.get("/chart-data", tags=["Admin Dashboard"])
async def get_chart_data(current_admin = Depends(get_current_admin)):
    """Get chart data for dashboard graphs"""
    admin_service = AdminService()
    chart_data = await admin_service.get_chart_data()
    return chart_data
