import os
import json
import base64
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from openai import OpenAI
from PIL import Image
import io
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EntityExtractionResult:
    """Data class for entity extraction results"""
    success: bool
    entities: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    image_info: Optional[Dict[str, Any]] = None

class ImageEntityExtractor:
    """Service for extracting entities from images using OpenAI's multimodal API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the service
        
        Args:
            api_key: OpenAI API key. If None, will try to get from environment
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1"  # GPT-4 with vision capabilities
        
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get basic image information
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with image metadata
        """
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": os.path.getsize(image_path)
                }
        except Exception as e:
            logger.error(f"Error getting image info: {str(e)}")
            return {}
    
    def _create_extraction_prompt(self) -> str:
        """
        Create the prompt for entity extraction
        
        Returns:
            Formatted prompt string
        """
        return """
        Analyze this image and extract all visible entities in a structured JSON format. 
        
        Please identify and categorize entities into the following types:
        - people: individuals visible in the image
        - objects: physical items, tools, furniture, etc.
        - animals: any animals or pets
        - vehicles: cars, bikes, planes, etc.
        - buildings: houses, stores, landmarks, etc.
        - nature: trees, flowers, landscapes, etc.
        - text: any readable text, signs, labels
        - food: meals, ingredients, beverages
        - clothing: garments, accessories
        - technology: computers, phones, electronics
        - other: anything that doesn't fit the above categories
        
        For each entity, provide:
        - name: descriptive name of the entity
        - category: one of the categories above
        - confidence: your confidence level (high/medium/low)
        - location: general location in image (e.g., "center", "top-left", "background")
        - description: brief description with relevant details
        - count: number of instances (if applicable)
        
        Return ONLY a valid JSON object with this structure:
        {
            "entities": [
                {
                    "name": "entity_name",
                    "category": "category_name",
                    "confidence": "high/medium/low",
                    "location": "location_description",
                    "description": "detailed_description",
                    "count": 1
                }
            ],
            "summary": {
                "total_entities": 0,
                "categories_found": [],
                "scene_description": "brief overall description"
            }
        }
        """
    
    def extract_entities(self, image_path: str) -> EntityExtractionResult:
        """
        Extract entities from an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            EntityExtractionResult with extracted entities or error info
        """
        try:
            # Validate image file exists
            if not os.path.exists(image_path):
                return EntityExtractionResult(
                    success=False,
                    error=f"Image file not found: {image_path}"
                )
            
            # Get image info
            image_info = self._get_image_info(image_path)
            
            # Encode image
            base64_image = self._encode_image(image_path)
            
            # Create the prompt
            prompt = self._create_extraction_prompt()
            
            # Make API call
            logger.info(f"Processing image: {image_path}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                entities_data = json.loads(content)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    entities_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from response")
            
            logger.info(f"Successfully extracted {len(entities_data.get('entities', []))} entities")
            
            return EntityExtractionResult(
                success=True,
                entities=entities_data,
                image_info=image_info
            )
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return EntityExtractionResult(
                success=False,
                error=str(e),
                image_info=image_info if 'image_info' in locals() else None
            )
    
    def extract_entities_from_url(self, image_url: str) -> EntityExtractionResult:
        """
        Extract entities from an image URL
        
        Args:
            image_url: URL of the image
            
        Returns:
            EntityExtractionResult with extracted entities or error info
        """
        try:
            # Create the prompt
            prompt = self._create_extraction_prompt()
            
            # Make API call
            logger.info(f"Processing image URL: {image_url}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                entities_data = json.loads(content)
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    entities_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from response")
            
            logger.info(f"Successfully extracted {len(entities_data.get('entities', []))} entities")
            
            return EntityExtractionResult(
                success=True,
                entities=entities_data,
                image_info={"source": "url", "url": image_url}
            )
            
        except Exception as e:
            logger.error(f"Error extracting entities from URL: {str(e)}")
            return EntityExtractionResult(
                success=False,
                error=str(e),
                image_info={"source": "url", "url": image_url}
            )
    
    def save_results(self, result: EntityExtractionResult, output_path: str) -> bool:
        """
        Save extraction results to a JSON file
        
        Args:
            result: EntityExtractionResult to save
            output_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_data = {
                "success": result.success,
                "entities": result.entities,
                "error": result.error,
                "image_info": result.image_info,
                "timestamp": str(datetime.now())
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            return False

# Example usage and CLI interface
def main():
    """Main function with example usage"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Extract entities from images using OpenAI API")
    parser.add_argument("image_path", help="Path to image file or image URL")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--url", action="store_true", help="Treat input as URL instead of file path")
    
    args = parser.parse_args()
    
    # Initialize service
    extractor = ImageEntityExtractor(api_key=args.api_key)
    
    # Extract entities
    if args.url:
        result = extractor.extract_entities_from_url(args.image_path)
    else:
        result = extractor.extract_entities(args.image_path)
    
    # Print results
    if result.success:
        print("✅ Entity extraction successful!")
        print(f"Found {len(result.entities.get('entities', []))} entities")
        print("\nExtracted entities:")
        print(json.dumps(result.entities, indent=2))
        
        # Save to file if specified
        if args.output:
            extractor.save_results(result, args.output)
    else:
        print("❌ Entity extraction failed!")
        print(f"Error: {result.error}")
    
    return result

if __name__ == "__main__":
    # Example usage without CLI
    # extractor = ImageEntityExtractor()
    # result = extractor.extract_entities("path/to/your/image.jpg")
    # print(json.dumps(result.entities, indent=2))
    
    main()
