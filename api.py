import os
import json
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import logging
from extract import ImageEntityExtractor, EntityExtractionResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Entity Extraction API",
    description="API for extracting entities from images using OpenAI's multimodal capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the entity extractor
extractor = ImageEntityExtractor()

# Pydantic models for request/response
class EntityRequest(BaseModel):
    """Request model for entity extraction from URL"""
    image_url: HttpUrl
    api_key: Optional[str] = None

class EntityResponse(BaseModel):
    """Response model for entity extraction"""
    success: bool
    entities: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    image_info: Optional[Dict[str, Any]] = None
    timestamp: str
    processing_time_ms: Optional[float] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str

class BatchEntityRequest(BaseModel):
    """Request model for batch entity extraction"""
    image_urls: List[HttpUrl]
    api_key: Optional[str] = None

class BatchEntityResponse(BaseModel):
    """Response model for batch entity extraction"""
    results: List[EntityResponse]
    total_processed: int
    successful: int
    failed: int
    timestamp: str

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Entity Extraction API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

@app.post("/extract/url", response_model=EntityResponse)
async def extract_entities_from_url(request: EntityRequest):
    """
    Extract entities from an image URL
    
    - **image_url**: URL of the image to analyze
    - **api_key**: Optional OpenAI API key (if not provided, uses environment variable)
    """
    start_time = datetime.now()
    
    try:
        # Use provided API key or default
        api_key = request.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        # Create extractor with API key
        url_extractor = ImageEntityExtractor(api_key=api_key)
        
        # Extract entities
        result = url_extractor.extract_entities_from_url(str(request.image_url))
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return EntityResponse(
            success=result.success,
            entities=result.entities,
            error=result.error,
            image_info=result.image_info,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in URL extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract/file", response_model=EntityResponse)
async def extract_entities_from_file(
    file: UploadFile = File(..., description="Image file to analyze"),
    api_key: Optional[str] = Form(None, description="Optional OpenAI API key")
):
    """
    Extract entities from an uploaded image file
    
    - **file**: Image file to upload and analyze
    - **api_key**: Optional OpenAI API key (if not provided, uses environment variable)
    """
    start_time = datetime.now()
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Use provided API key or default
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        # Create extractor with API key
        file_extractor = ImageEntityExtractor(api_key=api_key)
        
        # Save uploaded file temporarily
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Extract entities
            result = file_extractor.extract_entities(temp_file_path)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return EntityResponse(
                success=result.success,
                entities=result.entities,
                error=result.error,
                image_info=result.image_info,
                timestamp=datetime.now().isoformat(),
                processing_time_ms=processing_time
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"Error in file extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract/batch", response_model=BatchEntityResponse)
async def extract_entities_batch(request: BatchEntityRequest):
    """
    Extract entities from multiple image URLs in batch
    
    - **image_urls**: List of image URLs to analyze
    - **api_key**: Optional OpenAI API key (if not provided, uses environment variable)
    """
    start_time = datetime.now()
    
    try:
        # Use provided API key or default
        api_key = request.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        # Create extractor with API key
        batch_extractor = ImageEntityExtractor(api_key=api_key)
        
        results = []
        successful = 0
        failed = 0
        
        for url in request.image_urls:
            try:
                result = batch_extractor.extract_entities_from_url(str(url))
                results.append(EntityResponse(
                    success=result.success,
                    entities=result.entities,
                    error=result.error,
                    image_info=result.image_info,
                    timestamp=datetime.now().isoformat()
                ))
                if result.success:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                results.append(EntityResponse(
                    success=False,
                    error=str(e),
                    image_info={"source": "url", "url": str(url)},
                    timestamp=datetime.now().isoformat()
                ))
                failed += 1
        
        return BatchEntityResponse(
            results=results,
            total_processed=len(request.image_urls),
            successful=successful,
            failed=failed,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in batch extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def get_available_models():
    """Get information about available models"""
    return {
        "current_model": extractor.model,
        "available_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-vision-preview"
        ],
        "description": "Models with vision capabilities for image analysis"
    }

@app.post("/extract/url/simple")
async def extract_entities_simple(image_url: str = Form(..., description="Image URL")):
    """
    Simple endpoint for entity extraction from URL (form-based)
    
    - **image_url**: URL of the image to analyze
    """
    start_time = datetime.now()
    
    try:
        # Extract entities
        result = extractor.extract_entities_from_url(image_url)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "success": result.success,
            "entities": result.entities,
            "error": result.error,
            "processing_time_ms": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in simple extraction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 