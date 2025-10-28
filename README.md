# Second Brain

**Your local-first, AI-powered visual memory system for macOS**

Second Brain captures your screen continuously, extracts text with local OCR, generates AI summaries, and provides a beautiful UI for reviewing your digital life. All data stays on your Mac with industry-leading storage efficiency.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/macOS-11.0+-blue.svg)](https://www.apple.com/macos/)

---

## Highlights

- ** 100% Local OCR** – Apple Vision framework for instant text extraction (< 1s per frame)
- ** AI Summaries** – Automatic hourly summaries using GPT-5 (or GPT-4o-mini)
- ** 99% Storage Savings** – Smart capture + H.264 video compression (216 GB/day → 1.4 GB/day)
- ** Beautiful UI** – Streamlit-powered daily review with visual timeline
- ** Privacy First** – All processing local, data never leaves your Mac
- ** Blazing Fast** – 100x faster than cloud OCR, instant search
- ** Zero Cost** – No API fees for OCR, optional GPT for summaries

---

## 🚀 Quick Start

### Prerequisites

- macOS 11.0+ with screen recording permissions
- Python 3.11+
- ffmpeg (for video conversion): `brew install ffmpeg`
- OpenAI API key (optional, for AI summaries)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/gregcmartin/secondbrain.git
cd secondbrain

# 2. Create Python environment
python3.11 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 4. Configure (optional - for AI summaries)
cp .env.example .env
echo "OPENAI_API_KEY=sk-..." >> .env

# 5. Grant permissions
# System Settings → Privacy & Security → Screen Recording
# Enable for Terminal or your IDE
```

### Run

```bash
# Start capture service (runs in background)
second-brain start

# View your day in beautiful UI
second-brain ui

# Check status
second-brain status
```

---

## Features

### Smart Capture

- **Adaptive FPS**: 1.0 FPS when active, 0.2 FPS when idle (saves 80% during idle)
- **Frame Change Detection**: Skips duplicate frames automatically (30-50% savings)
- **Activity Monitoring**: Detects keyboard/mouse input to adjust capture rate
- **Disk Safeguards**: Configurable storage limits and free space monitoring

### Local OCR

- **Apple Vision Framework**: Native macOS OCR (same as Rewind)
- **Instant Processing**: < 1 second per frame
- **High Accuracy**: 95% confidence
- **Zero Cost**: No API fees
- **Privacy**: 100% local, data never leaves your Mac

### AI Summaries

- **Automatic**: Hourly summaries generated in background
- **GPT-5 Ready**: Uses GPT-5
- **Stored**: Summaries saved in database for instant access
- **Configurable**: Hourly/daily intervals
- **Raw Data Kept**: Original OCR text preserved

### Storage Optimization

- **Smart Capture**: 30-50% reduction via duplicate detection
- **Adaptive FPS**: 80% reduction during idle
- **Text Compression**: zlib for large text blocks (50-70% savings)
- **H.264 Video**: 96%+ compression for long-term storage
- **Combined**: 99.3% total savings (216 GB/day → 1.4 GB/day)

### Streamlit UI

- **Daily Overview**: AI-generated summaries and statistics
- **Visual Timeline**: Scroll through your day with frame thumbnails
- **Hourly Grouping**: Organized by hour for easy navigation
- **Frame Details**: Click any frame to see full image and OCR text
- **App Statistics**: See which apps you used most
- **Beautiful Design**: Gradient cards and responsive layout

### Search

- **Full-Text Search**: Fast FTS5 with trigram tokenization
- **Semantic Search**: Vector embeddings with Chroma + MiniLM
- **Filters**: By app, date range, time
- **CLI & UI**: Search from command line or Streamlit interface

---

## Storage Efficiency


```
Daily (smart capture):     37 GB/day (83% savings)
Daily (+ video conversion): 1.4 GB/day (99.3% savings)
Cost:                       $0/day (local OCR)
```


---

## CLI Reference

| Command | Description |
|---------|-------------|
| `second-brain start` | Start capture service (background) |
| `second-brain stop` | Stop capture service |
| `second-brain status` | Show system status and statistics |
| `second-brain ui` | Launch Streamlit UI (port 8501) |
| `second-brain timeline` | Launch React timeline UI (port 8000) |
| `second-brain query "term"` | Search captured text |
| `second-brain convert-to-video` | Convert frames to H.264 video |
| `second-brain health` | Check system health |

### Examples

```bash
# Search with filters
second-brain query "python code" --app "VSCode" --from 2025-10-20

# Semantic search
second-brain query "machine learning" --semantic

# Convert yesterday's frames to video
second-brain convert-to-video

# Convert specific date and keep originals
second-brain convert-to-video --date 2025-10-27 --keep-frames
```

---

## Data Storage

```
~/Library/Application Support/second-brain/
├── frames/              # Screenshots (PNG/WebP)
│   └── YYYY/MM/DD/
│       ├── HH-MM-SS-mmm.png
│       └── HH-MM-SS-mmm.json
├── videos/              # H.264 compressed videos
│   └── YYYY/MM/DD/
│       └── full_day.mp4
├── database/
│   ├── memory.db        # SQLite database
│   ├── memory.db-wal    # WAL file
│   └── memory.db-shm    # Shared memory
└── embeddings/          # Chroma vector store
    └── chroma/
```

---

## Configuration

Edit `~/.config/second-brain/settings.json` or use environment variables:

```json
{
  "capture": {
    "fps": 1.0,
    "format": "webp",
    "enable_frame_diff": true,
    "similarity_threshold": 0.95,
    "enable_adaptive_fps": true,
    "idle_fps": 0.2,
    "idle_threshold_seconds": 30.0,
    "max_disk_usage_gb": 100,
    "min_free_space_gb": 10
  },
  "ocr": {
    "recognition_level": "accurate",
    "batch_size": 5
  },
  "summarization": {
    "hourly_enabled": true,
    "daily_enabled": true,
    "min_frames": 10
  },
  "video": {
    "segment_duration_minutes": 5,
    "crf": 23,
    "preset": "medium",
    "delete_frames_after_conversion": false
  }
}
```

---

## Architecture

### Processing Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                      Second Brain                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Capture → OCR → Database → Embeddings → Summaries          │
│     │        │        │          │            │              │
│  Smart   Apple   SQLite    Chroma      GPT-5       │
│  Frame   Vision   WAL      MiniLM                            │
│  Diff    (local)  Compress                                   │
│                                                               │
│  ↓                                                            │
│  Streamlit UI ← Query API ← Search (FTS5 + Semantic)        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Capture Service**: Screenshots with smart frame diffing and adaptive FPS
2. **OCR Service**: Apple Vision framework for local text extraction
3. **Database**: SQLite with WAL mode, compression, and FTS5 search
4. **Embeddings**: Chroma vector store for semantic search
5. **Summarization**: GPT-5 for automatic activity summaries
6. **Video Converter**: ffmpeg for H.264 batch compression
7. **UI**: Streamlit for daily review and timeline browsing

---

## How It Works

### 1. Continuous Capture
- Captures screen at 1 FPS (or 0.2 FPS when idle)
- Skips duplicate frames automatically
- Saves as PNG/WebP with metadata JSON

### 2. Local OCR
- Apple Vision extracts text instantly
- Stores in SQLite with compression
- Indexes for full-text search

### 3. AI Summarization
- Every hour, generates summary of activity
- Uses GPT-5 (or GPT-4o-mini)
- Stores summaries in database

### 4. Long-Term Storage
- Run `convert-to-video` to compress old frames
- 96%+ compression with H.264
- Optionally delete originals to save space

### 5. Review & Search
- Use Streamlit UI for daily review
- Search with CLI or UI
- View any frame with OCR text

---

## Performance

### OCR Processing:
- **Speed**: < 1 second per frame
- **Accuracy**: 95% confidence
- **Success Rate**: 94%+ (750/797 frames)
- **Cost**: $0 (100% local)

### Storage Efficiency:
- **Frame Skipping**: Up to 100% during static content
- **Adaptive FPS**: 80% reduction when idle
- **Video Compression**: 96.25% (tested on 4,232 frames)
- **Database**: 17.93 MB for 797 frames + 750 text blocks

### System Resources:
- **CPU**: ~5% (local OCR is efficient)
- **Memory**: ~500 MB
- **Disk I/O**: Optimized with WAL mode
- **Network**: Zero for OCR, minimal for summaries

---

## Privacy & Security

- **100% Local OCR**: Text extraction never leaves your Mac
- **Local Storage**: All data in `~/Library/Application Support/second-brain/`
- **Optional Cloud**: Only for AI summaries (can be disabled)
- **No Tracking**: No telemetry, no analytics
- **Your Data**: You own it, you control it


---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Inspired by [Rewind](https://www.rewind.ai/) and [Screenpipe](https://github.com/mediar-ai/screenpipe)
- Built with Apple Vision framework, SQLite, and Python
- UI powered by Streamlit
- Video compression via ffmpeg


---

## Roadmap

- [x] Local OCR (Apple Vision)
- [x] Smart frame capture
- [x] Adaptive FPS
- [x] H.264 video compression
- [x] AI summarization
- [x] Streamlit UI
- [ ] Session reconstruction (stitch frames into video clips)
- [ ] Retention policies (auto-cleanup old data)
- [ ] Cloud sync (optional)

---

