"""
FreshRetail Forecasting API initialization.
"""

from fastapi import APIRouter  # Change from FastAPI to APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import API modules
from api.forecast import router as forecast_router
from api.promotions import router as promotions_router
from api.analytics_api import router as analytics_router
from api.enhanced_multi_modal_api import router as enhanced_router
from api.multi_dimensional_forecast import router as multi_dimensional_router
from api.clustering_segmentation import router as clustering_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create main API router
router = APIRouter(
    prefix="",  # Adjusted prefix as this will be included under /api in main.py
    tags=["Core API"],
)

# Remove CORS middleware from here, it should be in main.py
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Update this for production with specific origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Include routers from other modules
router.include_router(promotions_router, prefix="/promotions")
router.include_router(forecast_router, prefix="/forecast")
router.include_router(analytics_router, prefix="/analytics")
router.include_router(enhanced_router, prefix="/enhanced")
router.include_router(multi_dimensional_router, prefix="/multi-dimensional")
router.include_router(clustering_router, prefix="/clustering")


# Root endpoint
@router.get("/")  # Changed from @app.get
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the FreshRetail Forecasting API",
        "version": "1.0.0",
        "endpoints": {
            "forecast": "/api/forecast/",
            "promotions": "/api/promotions/",
            "analytics": "/api/analytics/",
            "enhanced": "/api/enhanced/",
            "multi-dimensional": "/api/multi-dimensional/",
            "clustering": "/api/clustering/",
        },
    }


# Health check endpoint
@router.get("/health")  # Changed from @app.get
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Export the router as 'app' for main.py to import
app = router

# Remove if __name__ == "__main__" block
# if __name__ == "__main__":
#     # This is used when running locally
#     import uvicorn

#     port = int(os.environ.get("PORT", 8000))
#     uvicorn.run(app, host="0.0.0.0", port=port)
