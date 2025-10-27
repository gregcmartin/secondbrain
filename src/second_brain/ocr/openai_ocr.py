"""OpenAI Vision API OCR implementation."""

import asyncio
import base64
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from openai import AsyncOpenAI, OpenAIError, RateLimitError

from ..config import Config

logger = structlog.get_logger()


class OpenAIOCR:
    """OCR service using OpenAI Vision API."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize OpenAI OCR service.
        
        Args:
            config: Configuration instance. If None, uses global config.
        """
        self.config = config or Config()
        
        # Get API key from environment
        api_key_env = self.config.get("ocr.api_key_env", "OPENAI_API_KEY")
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"OpenAI API key not found in environment variable: {api_key_env}")
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(api_key=api_key)
        
        # Configuration
        self.model = self.config.get("ocr.model", "gpt-5")
        self.max_retries = self.config.get("ocr.max_retries", 3)
        self.timeout = self.config.get("ocr.timeout_seconds", 30)
        self.include_semantic_context = self.config.get("ocr.include_semantic_context", True)
        
        # Rate limiting
        self.rate_limit_rpm = self.config.get("ocr.rate_limit_rpm", 50)
        self.min_request_interval = 60.0 / self.rate_limit_rpm
        self.last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        
        logger.info("openai_ocr_initialized", model=self.model, rate_limit_rpm=self.rate_limit_rpm)

    def _encode_image(self, image_path: Path) -> str:
        """Encode image to base64.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _build_prompt(self) -> str:
        """Build the vision prompt for text extraction.
        
        Returns:
            Prompt string for OpenAI Vision API
        """
        base_prompt = """Extract all visible text from this screenshot. 

Please provide:
1. All text content you can see, preserving the structure and layout
2. Identify the type of content (code, prose, UI elements, terminal output, etc.)
3. Note any important visual context (what application or type of interface this appears to be)

Format your response as JSON with this structure:
{
  "text": "all extracted text here",
  "block_type": "code|prose|terminal|ui_element|mixed",
  "semantic_context": "brief description of what's shown in the screenshot",
  "confidence": 0.0-1.0
}

Be thorough and accurate. If text is unclear, note it in the semantic_context."""

        if not self.include_semantic_context:
            base_prompt = base_prompt.replace(
                '"semantic_context": "brief description of what\'s shown in the screenshot",\n  ',
                ""
            )
        
        return base_prompt

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        async with self._rate_limit_lock:
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            
            if time_since_last_request < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last_request
                logger.debug("rate_limiting", sleep_seconds=sleep_time)
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = time.time()

    async def extract_text(
        self, image_path: Path, frame_id: str
    ) -> List[Dict[str, Any]]:
        """Extract text from an image using OpenAI Vision API.
        
        Args:
            image_path: Path to image file
            frame_id: Frame identifier
            
        Returns:
            List of text block dictionaries
        """
        if not image_path.exists():
            logger.error("image_not_found", path=str(image_path))
            return []
        
        # Encode image
        try:
            base64_image = self._encode_image(image_path)
        except Exception as e:
            logger.error("image_encoding_failed", path=str(image_path), error=str(e))
            return []
        
        # Build prompt
        prompt = self._build_prompt()
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Rate limiting
                await self._rate_limit()
                
                # Make API call
                logger.debug("ocr_request_starting", frame_id=frame_id, attempt=attempt + 1)
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    },
                                },
                            ],
                        }
                    ],
                    max_tokens=4096,
                    timeout=self.timeout,
                )
                
                # Parse response
                content = response.choices[0].message.content
                
                # Try to parse as JSON
                import json
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # If not JSON, treat entire response as text
                    result = {
                        "text": content,
                        "block_type": "mixed",
                        "confidence": 0.8,
                    }
                    if self.include_semantic_context:
                        result["semantic_context"] = "Raw text extraction"
                
                # Normalize text
                normalized_text = self._normalize_text(result.get("text", ""))
                
                # Create text block
                text_block = {
                    "block_id": str(uuid.uuid4()),
                    "frame_id": frame_id,
                    "text": result.get("text", ""),
                    "normalized_text": normalized_text,
                    "confidence": result.get("confidence", 0.9),
                    "block_type": result.get("block_type", "mixed"),
                }
                
                if self.include_semantic_context:
                    text_block["semantic_context"] = result.get("semantic_context", "")
                
                logger.info(
                    "ocr_completed",
                    frame_id=frame_id,
                    text_length=len(result.get("text", "")),
                    block_type=text_block["block_type"],
                )
                
                return [text_block]
                
            except RateLimitError as e:
                logger.warning(
                    "rate_limit_exceeded",
                    frame_id=frame_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("ocr_failed_rate_limit", frame_id=frame_id)
                    return []
                    
            except OpenAIError as e:
                logger.error(
                    "openai_api_error",
                    frame_id=frame_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    return []
                    
            except Exception as e:
                logger.error(
                    "ocr_unexpected_error",
                    frame_id=frame_id,
                    attempt=attempt + 1,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    return []
        
        return []

    def _normalize_text(self, text: str) -> str:
        """Normalize text by removing extra whitespace.
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        # Remove multiple spaces
        import re
        text = re.sub(r' +', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text

    async def process_batch(
        self, image_paths: List[tuple[Path, str]]
    ) -> List[List[Dict[str, Any]]]:
        """Process a batch of images.
        
        Args:
            image_paths: List of (image_path, frame_id) tuples
            
        Returns:
            List of text block lists (one per image)
        """
        processed_results: List[List[Dict[str, Any]]] = []
        for index, (image_path, frame_id) in enumerate(image_paths):
            try:
                processed_results.append(await self.extract_text(image_path, frame_id))
            except Exception as exc:
                logger.error(
                    "batch_processing_error",
                    index=index,
                    error=str(exc),
                )
                processed_results.append([])
        return processed_results
