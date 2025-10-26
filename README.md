# Visual Second Brain Roadmap

This project targets a Rewind-style, high-fidelity desktop memory system: local-first capture of the visual workspace, rich context extraction, and fast recall through search or replay. Below are two complementary build tracks—start with the CLI-first pipeline MVP, then graduate to a full timeline experience.

---

## Plan A · Pipeline MVP (CLI-first)

Goal: capture → OCR → index → query loop that runs entirely on macOS and proves the core value before UI investments.

- **Capture loop (Week 1)**
  - Use `screencapture -x` or a Quartz Display Services binding to grab 1–2 fps full-screen PNGs into `~/Library/Application Support/second-brain/frames/yyyy/mm/dd/`.
  - Store machine-readable metadata per frame: timestamp, active window title, app bundle id via Accessibility API (`AXUIElementCopyAttributeValue`).
  - Implement watchdog and disk quotas so the service pauses when free space drops below safety threshold.

- **OCR + text enrichment (Week 1–2)**
  - Run Apple VisionKit (preferred) or Tesseract with `--psm 6 --oem 1` over each frame, storing block-level coordinates.
  - Extract dominant colors / UI heuristics (code editor theme, dark/light mode).
  - Normalize text: dedupe whitespace, bucket into logical panes (window title, tab bar, main content, terminal output).

- **Storage + indexing (Week 2)**
  - Persist metadata in SQLite (or DuckDB) with three tables: `frames`, `text_blocks`, `windows`.
  - Attach an FTS5 virtual table over `text_blocks.content`, include trigram tokenization for partial matches.
  - Maintain derived embeddings (MiniLM or bge-small) in a local Chroma/FAISS index keyed by `frame_id`.

- **Query surface (Week 3)**
  - Ship a CLI (`second-brain query "<search string>"`) returning ranked matches with timestamps, window title, and preview path.
  - Add filters: app name, date range, code/project heuristics.
  - Optional: integrate with shell history (`fc -R`) to link terminal commands to matching frames.

- **Reliability + packaging (Week 4)**
  - Wrap capture & OCR workers in a launchd agent with crash recovery and status logging.
  - Expose simple health dashboard (`second-brain status`) including FPS, queue depth, disk usage.
  - Write integration tests using recorded sample frames to validate OCR pipeline determinism.

Outcome: text-searchable, timestamped memory feed you can interrogate from the terminal or downstream agents.

---

## Plan B · Capture + Timeline (UI-centric)

Goal: layer a navigable, high-resolution timeline and semantic recall UI on top of the pipeline data. Builds on Plan A artifacts.

- **Data streaming foundation (Week 5)**
  - Introduce gRPC/WebSocket service that streams new frame metadata + OCR payloads to clients.
  - Implement delta encoding for screenshot thumbnails (FFmpeg `-vf select='not(prev_selected_t+1<=t)'` or zstd patching) to reduce IO.
  - Add background job to generate low-res JPEG previews and 5-second video clips (via FFmpeg concat) for scrubbable playback.

- **Timeline viewer (Week 6–7)**
  - Use Tauri or Electron + React for desktop UI; emphasize low-latency load from SQLite/chroma.
  - Core UI affordances:
    - Zoomable timeline with heatmap density.
    - Hover previews + OCR text overlay.
    - Faceted filters (app, workspace/project tag, browser domain).
  - Implement keyboard-driven navigation (`j/k` to jump, `cmd+shift+f` to focus search).

- **Semantic recall layer (Week 7–8)**
  - Add natural-language search box powered by local LLM (e.g., llama.cpp, or API fallback).
  - Query plan: embed prompt, retrieve top N frames from vector store, rerank with a lightweight cross-encoder.
  - Support “session reconstruction”: stitch consecutive frames for the same window into a scrollable playback.

- **Context export & integrations (Week 8–9)**
  - Allow export of time slices to Markdown bundles: include OCR text, image preview, metadata JSON.
  - Integrate with ActivityWatch or Chrome extension to enrich history with URLs, repo paths, Git branches.
  - Provide plugin hooks for automation (e.g., trigger note in Obsidian when a “meeting” tag is detected).

- **Polish + privacy (Week 9+)**
  - Add local encryption at rest (SQLCipher) with keychain-backed credentials.
  - Surface retention policies: rolling purge, per-app exclusion, “incognito windows”.
  - Optional multiplayer: shared index across machines via Syncthing or custom replication protocol.

Outcome: self-hosted, high-resolution “visual memory” UI that rivals Rewind—searchable, replayable, and ready to feed agent workflows.

---

## Next Actions

1. Decide whether to start with the pipeline CLI or jump straight to the timeline stack.
2. Spin up a `docs/architecture/` folder to capture decisions, APIs, and data schema.
3. Bootstrap the capture daemon and storage schema; keep sample frames checked in for regression tests.
