#!/bin/bash

# Vehicle Counter - Quick Start Setup Script
# Supports: Windows (Git Bash), macOS, Linux

set -e

echo "=================================="
echo "Vehicle Counter - Setup & Launch"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check Python
print_status "Checking Python installation..."
if ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check Node.js
print_status "Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found. Please install Node.js 16+"
    exit 1
fi

NODE_VERSION=$(node --version)
print_success "Node.js $NODE_VERSION found"

# Create virtual environment
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
print_success "Virtual environment activated"

# Install Python dependencies
print_status "Installing Python dependencies (this may take a few minutes)..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Download YOLO model
print_status "Downloading YOLOv8 model (this may take a few minutes)..."
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" || print_warning "Could not auto-download YOLO, will download on first run"

print_success "Python setup complete"
echo ""

# Install Node dependencies
print_status "Installing Node.js dependencies..."
npm install
print_success "Node.js setup complete"
echo ""

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads results models
print_success "Directories created"
echo ""

# Summary
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "To run the application:"
echo ""
print_status "Development Mode (Full Integration):"
echo "  npm run full-dev"
echo ""
print_status "Or run components separately:"
echo "  Terminal 1: npm run backend"
echo "  Terminal 2: npm start"
echo "  Terminal 3: npm run electron"
echo ""
print_status "For testing backend only:"
echo "  npm run backend"
echo "  Then open: http://localhost:8000/docs"
echo ""
print_status "To build for distribution:"
echo "  npm run electron-build"
echo ""
echo "For more info, see SETUP_GUIDE.md"
echo ""
