#!/bin/bash

# Function to detect Python version
setup_python() {
    echo "Detecting Python installation..."
    # Look specifically for python3 versions
    PYTHON_VERSIONS=($(command -v python3 python3.* 2>/dev/null | sort -V))

    if [ ${#PYTHON_VERSIONS[@]} -eq 0 ]; then
        echo "No Python 3 installation found. Please install Python 3.11 or later."
        exit 1
    fi

    # Use the last (highest) version found
    PYTHON="${PYTHON_VERSIONS[-1]}"
    
    # Check Python version
    VERSION=$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$VERSION < 3.11" | bc -l) )); then
        echo "Python 3.11 or later is required. Found version $VERSION"
        exit 1
    fi

    echo "Using $PYTHON (version $VERSION)"
    return 0
}

# Check if virtual environment exists and activate it
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    if [ -n "$ZSH_VERSION" ]; then
        source .venv/bin/activate
    else
        . .venv/bin/activate
    fi
else
    echo "Virtual environment not found. Please run ./setup.sh first"
    exit 1
fi

# Setup Python and run the application
setup_python && python main.py
