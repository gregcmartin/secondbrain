# Second Brain - Setup Guide

## Prerequisites

- macOS (required for screen capture APIs)
- Python 3.11 or higher
- OpenAI API key

## Installation

### 1. Clone or Navigate to Project

```bash
cd /Users/gregcmartin/Desktop/Second\ Brain
```

### 2. Create Python Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Package in Development Mode

```bash
pip install -e .
```

### 5. Verify Installation

```bash
second-brain --help
```

## Configuration

### Environment Variables

The `.env` file has been created with your OpenAI API key. The system will automatically load it.

To modify settings, edit `~/.config/second-brain/settings.json` or use the default configuration.

### Default Configuration

```json
{
  "capture": {
    "fps": 1,
    "format": "png",
    "quality": 85,
    "max_disk_usage_gb": 100,
    "min_free_space_gb": 10
  },
  "ocr": {
    "engine": "openai",
    "model": "gpt-5",
    "api_key_env": "OPENAI_API_KEY",
    "batch_size": 5,
    "max_retries": 3,
    "rate_limit_rpm": 50,
    "include_semantic_context": true,
    "timeout_seconds": 30
  },
  "storage": {
    "retention_days": 90,
    "compression": true
  },
  "embeddings": {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "enabled": true
  }
}
```

## Data Storage

All data is stored locally in:
```
~/Library/Application Support/second-brain/
├── frames/          # Screenshot storage
├── database/        # SQLite database
├── embeddings/      # Vector embeddings
├── logs/           # Application logs
└── config/         # Configuration files
```

## Usage

### Start the Capture Service

```bash
second-brain start
```

### Check Status

```bash
second-brain status
```

### Search Your Memory

```bash
# Basic text search
second-brain query "search term"

# Search with app filter
second-brain query "search term" --app "VSCode"

# Search with date range
second-brain query "search term" --from "2025-10-20" --to "2025-10-26"

# Semantic search
second-brain query "search term" --semantic
```

### Stop the Service

```bash
second-brain stop
```

## Testing the OCR

You can test the OCR functionality with a sample screenshot:

```python
import asyncio
from pathlib import Path
from second_brain.ocr import OpenAIOCR

async def test_ocr():
    ocr = OpenAIOCR()
    
    # Take a test screenshot
    import subprocess
    test_path = Path("/tmp/test_screenshot.png")
    subprocess.run(["screencapture", "-x", str(test_path)])
    
    # Extract text
    results = await ocr.extract_text(test_path, "test-frame")
    
    for block in results:
        print(f"Text: {block['text'][:100]}...")
        print(f"Type: {block['block_type']}")
        print(f"Confidence: {block['confidence']}")
        if 'semantic_context' in block:
            print(f"Context: {block['semantic_context']}")

# Run test
asyncio.run(test_ocr())
```

## Troubleshooting

### API Key Issues

If you get an API key error:
1. Check that `.env` file exists in the project root
2. Verify the `OPENAI_API_KEY` is set correctly
3. Ensure you're running from the project directory or the `.env` is loaded

### Permission Issues

macOS may require permissions for:
- Screen Recording (System Preferences → Security & Privacy → Screen Recording)
- Accessibility (System Preferences → Security & Privacy → Accessibility)

### Rate Limiting

If you hit rate limits:
1. Reduce `capture.fps` in configuration
2. Increase `ocr.rate_limit_rpm` if your API tier allows
3. Check OpenAI API usage dashboard

## Next Steps

1. Implement the capture service (Week 1, Days 3-4)
2. Integrate OCR pipeline with capture loop (Week 1, Days 5-7)
3. Build CLI interface (Week 3)
4. Set up launchd for background service (Week 4)

## Cost Estimates

Based on 1 fps capture rate:
- ~3,600 screenshots per hour
- ~86,400 screenshots per day (24/7 capture)
- At $0.01 per 1,000 images (GPT-5 pricing): ~$0.86/day
- Recommended: Use lower fps (0.5 fps) for ~$0.43/day

Adjust `capture.fps` in configuration to control costs.
