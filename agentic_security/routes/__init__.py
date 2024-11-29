from .probe import router as probe_router
from .proxy import router as proxy_router
from .report import router as report_router
from .scan import router as scan_router
from .static import router as static_router

__all__ = [
    "static_router",
    "scan_router",
    "probe_router",
    "proxy_router",
    "report_router",
]
