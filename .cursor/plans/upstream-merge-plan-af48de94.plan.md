<!-- af48de94-7d7b-49b2-a023-333a4de976e9 52fc7967-b12d-4e67-8d77-660eb6f4e14b -->
# Fix Settings Panel and Reranker Integration

## Problems to Fix

1. **Settings panel takes too much sidebar space** - needs collapsible/expander
2. **Wrong settings exposed** - Manual FPS slider overrides smart auto-tuning
3. **Reranker not actually used** - CLI never passes rerank flag
4. **No README documentation** for reranker

## Implementation Plan

### Phase 1: Fix Settings Panel UI

Make the settings collapsible with an expander:

```python
with st.expander("⚙️ Settings", expanded=False):
    self.render_settings_panel()
```

### Phase 2: Expose the RIGHT Settings

#### Remove:

- Manual FPS slider (overrides smart auto-tuning!)

#### Keep/Add:

- **Smart Capture Toggles:**
  - Enable frame deduplication (`enable_frame_diff`)
  - Frame similarity threshold (`similarity_threshold`)
  - Enable adaptive FPS (`enable_adaptive_fps`)  
  - Idle detection threshold (`idle_threshold_seconds`)

- **Search Settings:**
  - Enable embeddings
  - Enable reranker (with model info)

- **Storage Settings:**
  - Retention days
  - Compression

### Phase 3: Actually Hook Up Reranker

#### In CLI (cli.py):

```python
# Add --reranker flag
@click.option('--reranker', is_flag=True, help='Use AI reranking for better relevance')

# Pass to search
matches = embedding_service.search(
    query=query,
    limit=limit,
    app_filter=app,
    rerank=reranker,  # ADD THIS!
)
```

### Phase 4: Document in README

Add section:

````markdown
## Search Options

### Reranking (Optional)
Improve search result relevance with AI-powered reranking:

```bash
# Enable reranking for better results
second-brain query "python code" --semantic --reranker
````

**Note:** Requires BAAI/bge-reranker-large model (2.24 GB download on first use)

To enable by default:

1. Run `second-brain ui`
2. Go to Settings → Search
3. Enable "Search result reranking"

```

## Files to Modify

1. **src/second_brain/ui/streamlit_app.py**

   - Wrap settings in expander
   - Remove manual FPS slider
   - Add smart capture toggles

2. **src/second_brain/cli.py**

   - Add `--reranker` flag
   - Pass `rerank=reranker` to search

3. **README.md**

   - Add reranker documentation
   - Explain smart capture features

## Expected Result

- Settings panel collapsible (not eating sidebar)
- Smart auto-tuning features preserved and configurable
- Reranker ACTUALLY WORKS when requested
- Users understand the features via README

### To-dos

- [ ] Create upstream-main-backup branch as safety net
- [ ] Extract reranker functionality from claude branch
- [ ] Extract settings API endpoints from claude branch
- [ ] Merge config.py changes carefully, keeping compatible features
- [ ] Remove all DeepSeek OCR references from user-facing parts
- [ ] Update README and documentation to match actual features
- [ ] Test reranker, settings API, and Streamlit UI
- [ ] Ensure no .venv files or broken imports remain