# Dashboard package
from .dashboard_routes import router
from .dashboard_service import DashboardService

__all__ = ["router", "DashboardService"]
