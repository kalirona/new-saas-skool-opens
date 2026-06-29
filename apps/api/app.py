#   _                          _   _
#  | |    ___  __ _ _ __ _ __ | | | | ___  _   _ ___  ___
#  | |   / _ \/ _` | '__| '_ \| |_| |/ _ \| | | / __|/ _ \
#  | |__|  __/ (_| | |  | | | |  _  | (_) | |_| \__ \  __/
#  |_____\___|\__,_|_|  |_| |_|_| |_|\___/ \__,_|___/\___|
#
#  LearnHouse · open-source learning platform · FastAPI entrypoint
#
#  ↳ learnhouse.app · github.com/learnhouse/learnhouse
#  ↳ Created and maintained by @swve © 2022–present

import logging

import uvicorn
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from config.branding import get_app_name
from config.config import LearnHouseConfig, get_learnhouse_config
from src.core.ee_hooks import register_ee_middlewares
from src.core.events.events import shutdown_app, startup_app
from src.core.middleware.cors import configure_cors
from src.core.middleware.security import SecurityHeadersMiddleware
from src.core.middleware.request_id import RequestIDMiddleware
from src.core.middleware.timing import RequestTimingMiddleware
from src.security.csrf import CSRFProtectionMiddleware
from src.router import v1_router
from src.routers.content_files import router as content_files_router
from src.routers.local_content import router as local_content_router


learnhouse_config: LearnHouseConfig = get_learnhouse_config()

if learnhouse_config.general_config.sentry_config.dsn:
    sentry_sdk.init(
        dsn=learnhouse_config.general_config.sentry_config.dsn,
        environment=learnhouse_config.general_config.env,
        send_default_pii=False,
        enable_logs=True,
        traces_sample_rate=1.0 if learnhouse_config.general_config.development_mode else 0.3,
        profile_session_sample_rate=1.0 if learnhouse_config.general_config.development_mode else 0.1,
        profile_lifecycle="trace",
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
    )

app = FastAPI(
    title=learnhouse_config.site_name,
    description=learnhouse_config.site_description,
    docs_url="/docs" if learnhouse_config.general_config.development_mode else None,
    redoc_url="/redoc" if learnhouse_config.general_config.development_mode else None,
    version="1.2.7",
)

# Middleware — order matters (outermost first)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestTimingMiddleware, slow_threshold_ms=1000.0)
configure_cors(app)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFProtectionMiddleware)
register_ee_middlewares(app)

# Lifecycle
app.add_event_handler("startup", startup_app(app))
app.add_event_handler("shutdown", shutdown_app(app))

# Content delivery — S3-aware router when S3 is enabled, local otherwise.
# Both paths enforce access control; neither serves raw StaticFiles.
if learnhouse_config.hosting_config.content_delivery.type == "s3api":
    app.include_router(content_files_router)
else:
    app.include_router(local_content_router)

app.include_router(v1_router)


@app.get("/")
async def root():
    return {"Message": f"Welcome to {get_app_name()} ✨"}


@app.get("/live", include_in_schema=False)
async def liveness():
    return {"status": "alive"}


@app.get("/ready", include_in_schema=False)
async def readiness(request: Request):
    import time
    from src.services.health.health import check_database
    from src.core.events.database import _async_session_factory
    start = time.monotonic()
    async with _async_session_factory() as db:
        result = await check_database(db)
    latency = (time.monotonic() - start) * 1000
    if result.status != "ok":
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not ready", "database": result.status, "latency_ms": latency})
    return {"status": "ready", "database": "ok", "latency_ms": latency}


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=learnhouse_config.hosting_config.port,
        reload=learnhouse_config.general_config.development_mode,
    )
