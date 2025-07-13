# Entity Extraction API

A FastAPI-based REST API for extracting entities from images using OpenAI's multimodal capabilities.

## Features

- 🖼️ **Image Analysis**: Extract entities from images using OpenAI's GPT-4 with vision
- 🌐 **URL Support**: Analyze images from URLs
- 📁 **File Upload**: Upload and analyze local image files
- 🔄 **Batch Processing**: Process multiple images at once
- 📊 **Structured Output**: Get detailed entity information in JSON format
- 🚀 **FastAPI**: Modern, fast web framework with automatic API documentation
- 🔒 **Flexible Auth**: Support for API keys in requests or environment variables

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using pipenv
pipenv install
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. Start the API Server

```bash
# Using the startup script
python start_api.py

# Or directly with uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Health Check
```http
GET /health
```

### Extract from URL
```http
POST /extract/url
Content-Type: application/json

{
  "image_url": "https://example.com/image.jpg",
  "api_key": "optional-api-key"
}
```

### Extract from File Upload
```http
POST /extract/file
Content-Type: multipart/form-data

file: [image file]
api_key: "optional-api-key"
```

### Batch Processing
```http
POST /extract/batch
Content-Type: application/json

{
  "image_urls": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg"
  ],
  "api_key": "optional-api-key"
}
```

### Simple URL Extraction (Form-based)
```http
POST /extract/url/simple
Content-Type: application/x-www-form-urlencoded

image_url=https://example.com/image.jpg
```

## Example Usage

### Using curl

```bash
# Extract from URL
curl -X POST "http://localhost:8000/extract/url" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg"
  }'

# Upload file
curl -X POST "http://localhost:8000/extract/file" \
  -F "file=@/path/to/your/image.jpg"

# Batch processing
curl -X POST "http://localhost:8000/extract/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "image_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }'
```

### Using Python

```python
import requests

# Extract from URL
response = requests.post(
    "http://localhost:8000/extract/url",
    json={
        "image_url": "https://example.com/image.jpg"
    }
)
result = response.json()
print(result)

# Upload file
with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/extract/file",
        files={"file": f}
    )
result = response.json()
print(result)
```

## Response Format

```json
{
  "success": true,
  "entities": {
    "entities": [
      {
        "name": "person",
        "category": "people",
        "confidence": "high",
        "location": "center",
        "description": "A person wearing a red shirt",
        "count": 1
      }
    ],
    "summary": {
      "total_entities": 1,
      "categories_found": ["people"],
      "scene_description": "A person in a room"
    }
  },
  "image_info": {
    "width": 1920,
    "height": 1080,
    "format": "JPEG",
    "mode": "RGB",
    "size_bytes": 123456
  },
  "timestamp": "2024-01-01T12:00:00",
  "processing_time_ms": 1500.5
}
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `API_HOST`: Server host (default: 0.0.0.0)
- `API_PORT`: Server port (default: 8000)
- `API_RELOAD`: Enable auto-reload (default: false)

### Model Configuration

The API uses GPT-4 with vision capabilities by default. You can modify the model in `extract.py`:

```python
self.model = "gpt-4o"  # or "gpt-4o-mini", "gpt-4-turbo", etc.
```

## Entity Categories

The API extracts entities in the following categories:

- **people**: Individuals visible in the image
- **objects**: Physical items, tools, furniture, etc.
- **animals**: Any animals or pets
- **vehicles**: Cars, bikes, planes, etc.
- **buildings**: Houses, stores, landmarks, etc.
- **nature**: Trees, flowers, landscapes, etc.
- **text**: Any readable text, signs, labels
- **food**: Meals, ingredients, beverages
- **clothing**: Garments, accessories
- **technology**: Computers, phones, electronics
- **other**: Anything that doesn't fit the above categories

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (missing API key, invalid URL, etc.)
- `500`: Internal server error

Error responses include:
```json
{
  "error": "Error description",
  "timestamp": "2024-01-01T12:00:00",
  "path": "/extract/url"
}
```

## Development

### Running in Development Mode

```bash
export API_RELOAD=true
python start_api.py
```

### Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with a sample image URL
curl -X POST "http://localhost:8000/extract/url" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://picsum.photos/400/300"}'
```

## License

This project is open source and available under the MIT License. 