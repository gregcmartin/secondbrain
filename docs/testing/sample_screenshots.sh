#!/bin/bash
# Sample random screenshots from captured frames for manual inspection

set -e

FRAMES_DIR="$HOME/Library/Application Support/second-brain/frames"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLES_DIR="$SCRIPT_DIR/screenshots"
NUM_SAMPLES=10

echo "================================"
echo "Screenshot Sampling Tool"
echo "================================"
echo ""

# Check if frames directory exists
if [ ! -d "$FRAMES_DIR" ]; then
    echo "❌ Error: Frames directory not found at $FRAMES_DIR"
    echo "   Please run a capture test first with: ./run_test_capture.sh"
    exit 1
fi

# Count total frames
TOTAL_FRAMES=$(find "$FRAMES_DIR" -type f -name "*.png" | wc -l | tr -d ' ')

if [ "$TOTAL_FRAMES" -eq 0 ]; then
    echo "❌ Error: No PNG frames found in $FRAMES_DIR"
    exit 1
fi

echo "Found $TOTAL_FRAMES total frames"
echo "Sampling $NUM_SAMPLES random frames..."
echo ""

# Create samples directory
mkdir -p "$SAMPLES_DIR"

# Get random sample of frames
SAMPLED=0
find "$FRAMES_DIR" -type f -name "*.png" | \
    shuf -n $NUM_SAMPLES | \
    while read -r frame_path; do
        SAMPLED=$((SAMPLED + 1))
        frame_name=$(basename "$frame_path")
        frame_date=$(dirname "$frame_path" | xargs basename)

        # Copy frame to samples directory with descriptive name
        sample_name="sample_${SAMPLED}_${frame_date}_${frame_name}"
        cp "$frame_path" "$SAMPLES_DIR/$sample_name"

        # Also copy the JSON metadata if it exists
        json_path="${frame_path%.png}.json"
        if [ -f "$json_path" ]; then
            cp "$json_path" "$SAMPLES_DIR/${sample_name%.png}.json"
        fi

        echo "✅ Sampled: $frame_name (from $frame_date)"
    done

echo ""
echo "✅ Sampling complete!"
echo "   Samples saved to: $SAMPLES_DIR"
echo ""
echo "You can now:"
echo "  - Open sample images to verify capture quality"
echo "  - Check JSON files for OCR text and metadata"
echo "  - Use these for manual testing validation"
