#!/bin/bash
# Automated 5-minute screen capture test for Second Brain

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCREENSHOTS_DIR="$SCRIPT_DIR/screenshots"
TEST_DURATION=300  # 5 minutes in seconds

echo "================================"
echo "Second Brain - 5-Minute Capture Test"
echo "================================"
echo ""
echo "Test Configuration:"
echo "- Duration: 5 minutes ($TEST_DURATION seconds)"
echo "- Screenshots will be saved to: $SCREENSHOTS_DIR"
echo "- Test timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Clean screenshot directory
rm -rf "$SCREENSHOTS_DIR"
mkdir -p "$SCREENSHOTS_DIR"

# Check if second-brain service is already running
if pgrep -f "second-brain" > /dev/null; then
    echo "⚠️  Second Brain service is already running. Stopping it first..."
    second-brain stop
    sleep 2
fi

# Start second-brain service
echo "🚀 Starting Second Brain capture service..."
second-brain start

# Wait for service to initialize
sleep 5

echo ""
echo "✅ Service started. Beginning 5-minute test..."
echo ""
echo "Please perform various activities:"
echo "  - Browse different websites"
echo "  - Open/switch applications"
echo "  - Write some code or documents"
echo "  - Use different apps (Terminal, VS Code, Browser, etc.)"
echo ""
echo "The test will automatically stop in 5 minutes."
echo ""

# Progress indicator
ELAPSED=0
INTERVAL=30  # Update every 30 seconds

while [ $ELAPSED -lt $TEST_DURATION ]; do
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    REMAINING=$((TEST_DURATION - ELAPSED))
    echo "⏱️  Test in progress... ${ELAPSED}s elapsed, ${REMAINING}s remaining"
done

echo ""
echo "⏹️  5 minutes completed. Stopping capture service..."
second-brain stop

# Wait for service to fully stop
sleep 3

echo ""
echo "📊 Collecting test statistics..."
second-brain status

echo ""
echo "✅ Test capture complete!"
echo ""
echo "Next steps:"
echo "1. Review captured frames in ~/Library/Application Support/second-brain/frames/"
echo "2. Run query tests with: second-brain query <search-term>"
echo "3. Check database entries"
echo ""
echo "Test completed at: $(date '+%Y-%m-%d %H:%M:%S')"
