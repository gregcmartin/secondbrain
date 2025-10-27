#!/bin/bash
# Installation script for Second Brain

set -e

echo "🧠 Second Brain Installation Script"
echo "===================================="
echo ""

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ Error: This script only works on macOS"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Error: Python 3.11 is required but not found"
    echo "Please install Python 3.11 first:"
    echo "  brew install python@3.11"
    exit 1
fi

echo "✓ Python 3.11 found"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install package
echo ""
echo "Installing Second Brain..."
pip install -e .

# Check for OpenAI API key
echo ""
if [ -f ".env" ]; then
    echo "✓ .env file found"
else
    echo "⚠️  Warning: .env file not found"
    echo "Please create .env file with your OpenAI API key:"
    echo "  OPENAI_API_KEY=your-key-here"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p ~/Library/Application\ Support/second-brain/{frames,database,embeddings,logs,config}
echo "✓ Directories created"

# Install launchd service (optional)
echo ""
read -p "Install as launchd service (auto-start on login)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing launchd service..."
    
    # Copy plist to LaunchAgents
    cp com.secondbrain.capture.plist ~/Library/LaunchAgents/
    
    # Load service
    launchctl load ~/Library/LaunchAgents/com.secondbrain.capture.plist
    
    echo "✓ Service installed and started"
    echo "  To stop: launchctl unload ~/Library/LaunchAgents/com.secondbrain.capture.plist"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Check health: second-brain health"
echo "3. Start service: second-brain start"
echo "4. Search memory: second-brain query \"search term\""
echo ""
echo "For more information, see docs/SETUP.md"
