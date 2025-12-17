#!/bin/bash

# FFmpeg Wizard Setup Script

echo "🎬 FFmpeg Wizard Setup"
echo "======================"
echo ""

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg is not installed!"
    echo ""
    echo "Please install FFmpeg:"
    echo "  macOS:   brew install ffmpeg"
    echo "  Linux:   sudo apt-get install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org"
    echo ""
    exit 1
else
    echo "✅ FFmpeg is installed"
    ffmpeg -version | head -n 1
fi

echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION"
fi

echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your API keys!"
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env << EOF
# OpenAI API Key for LLM analysis
OPENAI_API_KEY=your_openai_api_key_here

# Pexels API Key for stock video search
PEXELS_API_KEY=your_pexels_api_key_here

# Optional: Use CUDA for faster Whisper processing (set to 'cuda' if available)
WHISPER_DEVICE=cpu
WHISPER_MODEL=small
EOF
        echo "✅ Created .env file"
        echo "⚠️  Please edit .env and add your API keys!"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys (optional for basic features)"
echo "  2. Run: streamlit run app.py"
echo "  3. Or use CLI: python main.py input_video.mp4 -o output.mp4"
echo ""

