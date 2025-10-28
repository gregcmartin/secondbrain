# Second Brain Testing Suite

This directory contains comprehensive testing scripts and documentation for validating the reranker feature and overall system functionality.

## Testing Scripts

### 1. `run_test_capture.sh`
Automated 5-minute screen capture test.

**Usage:**
```bash
./run_test_capture.sh
```

**What it does:**
- Starts second-brain capture service
- Runs for exactly 5 minutes
- Shows progress updates every 30 seconds
- Stops service and displays statistics
- Prompts you to perform various activities during capture

**Requirements:**
- Second Brain must be installed
- OPENAI_API_KEY must be set in environment

---

### 2. `sample_screenshots.sh`
Samples 10 random screenshots from captured frames for manual inspection.

**Usage:**
```bash
./sample_screenshots.sh
```

**What it does:**
- Finds all captured PNG frames
- Randomly selects 10 samples
- Copies samples and their JSON metadata to `screenshots/`
- Provides file list for manual review

**Output:**
- Screenshots saved to: `docs/testing/screenshots/`
- Each sample includes the frame image and OCR metadata

---

### 3. `run_query_tests.sh`
Runs comparative query tests with and without reranker.

**Usage:**
```bash
./run_query_tests.sh
```

**What it does:**
- Tests 5 predefined queries: "code", "browser", "terminal", "python", "search"
- Runs each query twice:
  1. Baseline (semantic search only)
  2. With reranker enabled
- Saves results to separate markdown files
- Includes timestamps and full query output

**Output:**
- `baseline_queries.md` - Results without reranker
- `reranker_queries.md` - Results with reranker enabled

---

## Testing Workflow

### Complete Test Sequence

```bash
# 1. Clean slate (if needed)
rm -rf "$HOME/Library/Application Support/second-brain"

# 2. Run 5-minute capture test
./run_test_capture.sh

# 3. Sample random screenshots for inspection
./sample_screenshots.sh

# 4. Run query tests (both baseline and reranker)
./run_query_tests.sh

# 5. Review results
cat baseline_queries.md
cat reranker_queries.md
```

### Manual Testing Checklist

- [ ] Verify captured frames exist in `~/Library/Application Support/second-brain/frames/`
- [ ] Check database has entries: `second-brain status`
- [ ] Review sampled screenshots for quality
- [ ] Compare baseline vs reranker query results
- [ ] Test UI settings panel: `second-brain ui`
- [ ] Enable/disable reranker in UI and verify persistence
- [ ] Run Playwright tests: `pytest tests/test_e2e_settings.py`
- [ ] Run E2E test script: `./tests/test_e2e_full.sh`

---

## Test Queries Explained

The query tests use these terms to validate different search scenarios:

- **"code"** - Should find programming-related screens
- **"browser"** - Should find web browsing activity
- **"terminal"** - Should find command-line activity
- **"python"** - Should find Python code or documentation
- **"search"** - Should find search-related screens

Feel free to modify `run_query_tests.sh` to add your own test queries.

---

## Expected Results

### Baseline (No Reranker)
- Fast results (vector similarity only)
- May include less relevant matches
- Distance-based ranking

### With Reranker
- Slightly slower (cross-encoder scoring)
- More relevant results
- Semantic reranking based on query-document pairs
- Should show improved relevance for ambiguous queries

---

## Troubleshooting

**Service won't start:**
```bash
# Check if already running
ps aux | grep second-brain

# Stop any existing instances
second-brain stop
```

**No frames captured:**
```bash
# Check system logs
cat "$HOME/Library/Application Support/second-brain/logs"/*.log

# Verify OpenAI API key
echo $OPENAI_API_KEY
```

**Query returns no results:**
- Ensure you performed activities during the 5-minute test
- Check database has entries: `second-brain status`
- Try semantic search: `second-brain query "test" --semantic`

---

## Files Generated

All testing artifacts are git-ignored (see `.gitignore`):

```
docs/testing/
├── screenshots/           # Sampled frames (git-ignored)
├── baseline_queries.md    # Query results without reranker (git-ignored)
├── reranker_queries.md    # Query results with reranker (git-ignored)
├── TEST_RESULTS.md        # Comprehensive test documentation (git-ignored)
├── run_test_capture.sh    # Capture test script
├── sample_screenshots.sh  # Screenshot sampling script
├── run_query_tests.sh     # Query test script
└── README.md              # This file
```

---

## Notes

- **Privacy:** All test data stays local. Screenshots and OCR text are never uploaded.
- **Duration:** Full test suite takes ~15 minutes (5 min capture + sampling + queries)
- **Storage:** Expect ~500MB-1GB of test data per 5-minute capture
- **Cleanup:** Use `second-brain reset --yes` to delete all test data
