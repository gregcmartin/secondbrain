"""OCR module for Second Brain.

Uses Apple Vision framework for local, fast, free OCR.
"""

from .apple_vision_ocr import AppleVisionOCR

# Default OCR is Apple Vision (local, fast, free)
OCR = AppleVisionOCR

__all__ = ["AppleVisionOCR", "OCR"]
