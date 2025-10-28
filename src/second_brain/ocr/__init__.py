"""OCR module for Second Brain.

Supports both local (Apple Vision) and cloud (OpenAI) OCR.
Default is Apple Vision for speed, privacy, and zero cost.
"""

from .apple_vision_ocr import AppleVisionOCR
from .openai_ocr import OpenAIOCR

# Use Apple Vision OCR by default (local, fast, free)
OCR = AppleVisionOCR

__all__ = ["AppleVisionOCR", "OpenAIOCR", "OCR"]
