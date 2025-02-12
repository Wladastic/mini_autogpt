#!/bin/bash
set -e

echo "Setting up Mini-AutoGPT development environment..."

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
    PYTHON="${PYTHON_VERSIONS[${#PYTHON_VERSIONS[@]}-1]}"
    
    # Check Python version
    VERSION=$($PYTHON -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$VERSION < 3.11" | bc -l) )); then
        echo "Python 3.11 or later is required. Found version $VERSION"
        exit 1
    fi

    echo "Using $PYTHON (version $VERSION)"
}

# Create and activate virtual environment
setup_venv() {
    echo "Creating virtual environment..."
    $PYTHON -m venv .venv
    
    # Source the appropriate activate script based on the shell
    if [ -n "$ZSH_VERSION" ]; then
        source .venv/bin/activate
    else
        . .venv/bin/activate
    fi

    if [ $? -ne 0 ]; then
        echo "Failed to create/activate virtual environment"
        exit 1
    fi

    echo "Virtual environment created and activated"
}

# Install dependencies
install_dependencies() {
    echo "Installing dependencies..."
    python -m pip install --upgrade pip setuptools wheel
    python -m pip install -r requirements.txt
}

# Create .env file if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        echo "Creating .env file from template..."
        cp .env.template .env
        echo "Please update the .env file with your configuration"
    fi
}

# Main setup process
main() {
    setup_python
    setup_venv
    echo "Activating virtual environment..."
    if [ -n "$ZSH_VERSION" ]; then
        source .venv/bin/activate
    else
        . .venv/bin/activate
    fi
    install_dependencies
    setup_env
    
    echo "Setup complete! Your development environment is ready."
    echo "To start working:"
    echo "1. Update the .env file with your configuration"
    echo "2. Run './run.sh' to start the application"
}

main
