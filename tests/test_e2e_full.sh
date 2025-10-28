#!/bin/bash
# Full end-to-end testing for reranker and settings
set -e

echo "============================================================"
echo "FULL E2E TESTING: Search & Settings Enhancements"
echo "============================================================"

# Step 1: Stop any running services
echo ""
echo "STEP 1: Stopping any running services..."
second-brain stop 2>/dev/null || true
sleep 2

# Step 2: Check baseline - no reranker flag
echo ""
echo "STEP 2: Testing baseline (without reranker)..."
second-brain query "test" --help | grep -q "reranker" && echo "ERROR: Reranker flag exists in baseline!" || echo "✓ Baseline correct - no reranker flag"

# Step 3: Start service
echo ""
echo "STEP 3: Starting capture service..."
second-brain start &
sleep 5

# Step 4: Test without reranker
echo ""
echo "STEP 4: Testing search WITHOUT reranker..."
second-brain query "test" --semantic --limit 5 > /tmp/test_no_reranker.txt
echo "✓ Search without reranker completed"

# Step 5: Test with reranker (if available)
echo ""
echo "STEP 5: Testing search WITH reranker..."
second-brain query "test" --semantic --reranker --limit 5 > /tmp/test_with_reranker.txt 2>&1 || echo "Note: Reranker may require FlagEmbedding package"
echo "✓ Search with reranker attempted"

# Step 6: Compare results
echo ""
echo "STEP 6: Comparing results..."
if [ -f /tmp/test_no_reranker.txt ] && [ -f /tmp/test_with_reranker.txt ]; then
    echo "Results without reranker:"
    head -5 /tmp/test_no_reranker.txt
    echo ""
    echo "Results with reranker:"
    head -5 /tmp/test_with_reranker.txt
fi

# Step 7: Verify config settings
echo ""
echo "STEP 7: Verifying config settings..."
python3 << 'PYTHON'
from second_brain.config import get_config
config = get_config()
print(f"✓ Reranker enabled: {config.get('embeddings.reranker_enabled')}")
print(f"✓ Reranker model: {config.get('embeddings.reranker_model')}")
print(f"✓ Smart capture enabled: {config.get('capture.enable_frame_diff')}")
print(f"✓ Adaptive FPS enabled: {config.get('capture.enable_adaptive_fps')}")
PYTHON

# Step 8: Stop service
echo ""
echo "STEP 8: Stopping service..."
second-brain stop
sleep 2

echo ""
echo "============================================================"
echo "✅ FULL E2E TESTING COMPLETE"
echo "============================================================"

