from .core.app import create_app
from .core.logging import setup_logging
from .middleware.cors import setup_cors
from .middleware.logging import LogNon200ResponsesMiddleware
from .routes import (
    probe_router,
    proxy_router,
    report_router,
    scan_router,
    static_router,
    telemetry,
)

# Create the FastAPI app
app = create_app()

# Setup middleware
setup_cors(app)
app.add_middleware(LogNon200ResponsesMiddleware)

# Setup logging
setup_logging()

# Register routers
app.include_router(static_router)
app.include_router(scan_router)
app.include_router(probe_router)
app.include_router(proxy_router)
app.include_router(report_router)
telemetry.setup(app)
