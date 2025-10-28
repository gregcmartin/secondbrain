#!/bin/bash
# Run query tests with and without reranker for comparison

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASELINE_FILE="$SCRIPT_DIR/baseline_queries.md"
RERANKER_FILE="$SCRIPT_DIR/reranker_queries.md"

# Test queries
QUERIES=(
    "code"
    "browser"
    "terminal"
    "python"
    "search"
)

echo "================================"
echo "Query Testing: Baseline vs Reranker"
echo "================================"
echo ""

# Function to run queries and save results
run_queries() {
    local mode=$1
    local output_file=$2
    local reranker_flag=$3

    echo "# Query Test Results - $mode" > "$output_file"
    echo "" >> "$output_file"
    echo "**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')" >> "$output_file"
    echo "**Mode:** $mode" >> "$output_file"
    echo "" >> "$output_file"
    echo "---" >> "$output_file"
    echo "" >> "$output_file"

    for query in "${QUERIES[@]}"; do
        echo "  Testing query: '$query' ($mode)"

        echo "## Query: \"$query\"" >> "$output_file"
        echo "" >> "$output_file"
        echo "\`\`\`bash" >> "$output_file"
        echo "second-brain query \"$query\" --semantic $reranker_flag --limit 5" >> "$output_file"
        echo "\`\`\`" >> "$output_file"
        echo "" >> "$output_file"
        echo "### Results:" >> "$output_file"
        echo "" >> "$output_file"
        echo "\`\`\`" >> "$output_file"

        # Run the query and capture output
        second-brain query "$query" --semantic $reranker_flag --limit 5 2>&1 >> "$output_file" || echo "Query failed" >> "$output_file"

        echo "\`\`\`" >> "$output_file"
        echo "" >> "$output_file"
        echo "---" >> "$output_file"
        echo "" >> "$output_file"

        # Small delay between queries
        sleep 2
    done

    echo "✅ $mode testing complete"
    echo ""
}

# Test 1: Baseline (no reranker)
echo "📊 Phase 1: Baseline queries (no reranker)"
echo ""
run_queries "Baseline (No Reranker)" "$BASELINE_FILE" ""

# Test 2: With reranker
echo "📊 Phase 2: Queries with reranker"
echo ""
run_queries "With Reranker" "$RERANKER_FILE" "--reranker"

echo "================================"
echo "✅ All query tests complete!"
echo "================================"
echo ""
echo "Results saved to:"
echo "  Baseline: $BASELINE_FILE"
echo "  Reranker: $RERANKER_FILE"
echo ""
echo "Next steps:"
echo "1. Compare results between baseline and reranker"
echo "2. Note relevance improvements"
echo "3. Document findings in TEST_RESULTS.md"
