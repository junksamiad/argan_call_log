from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_airtable
from backend.api.endpoints import webhook
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Argan HR Email Management System",
    description="API for managing HR email queries with SendGrid integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Airtable connection on startup
@app.on_event("startup")
async def startup_event():
    try:
        init_airtable()
        logger.info("Airtable connection initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Airtable: {str(e)}")

# Include webhook router for SendGrid
app.include_router(webhook.router, tags=["Webhook"])  # No prefix - SendGrid expects /inbound

@app.get("/")
async def root():
    return {
        "message": "Argan HR Email Management System API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 