import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import Logger, app_logger
from app.core.exceptions import (
    AIDataAnalyticsException,
    database_exception_handler,
    validation_exception_handler,
    response_validation_exception_handler,
    ai_data_analytics_exception_handler,
    general_exception_handler,
    http_exception_handler,
)
from app.middleware.logging_middleware import LoggingMiddleware, SecurityLoggingMiddleware
from app.middleware.api_history_middleware import APIHistoryMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.tasks.cleanup_tasks import schedule_cleanup_tasks
from app.api.v1.endpoints.auth import router as authrouter



# Import and include specific routers to avoid conflicts
import importlib
import pkgutil

def include_routers_from_folder(app: FastAPI, package: str,path: str, excluded_modules: list = None):
    """
    Dynamically import all modules in the given package and include their routers.
    Excludes specified modules to avoid conflicts.
    """
    apilist = ""
    app_logger.info(f"Including routers from package: {package}, path prefix: /{path}")
    if excluded_modules is None:
        excluded_modules = []
    
    package_path = package.replace(".", "/")
    for _, module_name, _ in pkgutil.iter_modules([package_path]):
        if module_name in excluded_modules:
            app_logger.info(f"Skipping excluded module: {module_name}")
            continue
            
        try:
            module = importlib.import_module(f"{package}.{module_name}")
            if hasattr(module, "router"):
                app.include_router(module.router, prefix=f"/{path}/{module_name}")
                app_logger.info(f"Included router from {module_name} with prefix /{path}/{module_name}")
                # list endpoints for debugging/logging
                #app_logger.debug(f"🔹 Endpoints in module '{module_name}':")
                for route in module.router.routes:
                    apilist = f"{apilist} {route.methods},/{path}/{module_name}/{route.path} \n"                    
                    app_logger.info(f"The router method {route.methods} is added with the router pathe:/{path}/{module_name}/{route.path}")

            
            
        except Exception as e:
            app_logger.warning(f"Failed to import router from {module_name}: {e}")

    app_logger.debug(f"API Calls List: {apilist} \n")

@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = None
    try:
        # Initialize logging
        Logger.info("Starting AI Data Analytics Platform")

        # Initialize database
        await init_db()
        Logger.info("Database initialized successfully")

        # Start background cleanup task
        cleanup_task = asyncio.create_task(schedule_cleanup_tasks())
        Logger.info("Background cleanup task started")

        yield

    except Exception as e:
        Logger.error(f"Error during startup: {e}")
        raise
    finally:
        # Cleanup on shutdown
        Logger.info("Shutting down AI Data Analytics Platform")

        # Cancel background tasks
        if cleanup_task and not cleanup_task.done():
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        # Wait briefly for any active SSE connections to close
        Logger.info("Waiting for active connections to close...")
        await asyncio.sleep(1)

        Logger.info("Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered data analytics platform",
    version=settings.VERSION,
    openapi_url=f"{settings.API_STR}/openapi.json",
    lifespan=lifespan
)

app_logger.debug("Add middleware")
# Add middleware (order matters - add before CORS)
app.add_middleware(RateLimitMiddleware)  # Rate limiting and cost control
app.add_middleware(APIHistoryMiddleware)  # Temporarily disabled due to async session issue
app.add_middleware(LoggingMiddleware)  # Temporarily disabled for testing
app.add_middleware(SecurityLoggingMiddleware)  # Temporarily disabled for testing

# Set up CORS
# Add exception handlers
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)
app.add_exception_handler(AIDataAnalyticsException, ai_data_analytics_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app_logger.debug ("Start API Router")
app.include_router(authrouter, prefix=settings.API_STR+"/auth")
# Include API router
app.include_router(api_router, prefix=settings.API_STR)
# Include Text2SQL router for AI-powered features
#app.include_router(text2sql_router, prefix=settings.API_STR+"/text2sql", tags=["text2sql"])


@app.get("/")
async def root():
    return {"message": "AI Data Analytics Platform API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app_logger.debug("App starting completed")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
