#!/bin/bash

# Create required directories
echo "Creating benchmark directories..."
mkdir -p benchmark/results
mkdir -p benchmark/visualizations
mkdir -p benchmark/reports
mkdir -p benchmark/logs
mkdir -p benchmark/mock_data

# Make script executable
chmod +x benchmark/setup.sh

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

# Create empty __init__.py files
echo "Initializing Python package..."
touch benchmark/__init__.py

# Create .env if it doesn't exist
if [ ! -f benchmark/.env ]; then
    echo "Creating default .env file..."
    echo "# Benchmark Configuration" > benchmark/.env
    echo "BENCHMARK_DEBUG=true" >> benchmark/.env
    echo "BENCHMARK_LOG_LEVEL=DEBUG" >> benchmark/.env
fi

echo "✅ Benchmark system setup complete!"
echo ""
echo "Available commands:"
echo "🔍 Run 'python -m benchmark.runner' to start benchmarking"
echo "🧪 Run 'python -m benchmark.test_scenarios' to generate test data"
echo "📊 Run 'python -m benchmark.visualizer' to create visualizations"
echo "📝 Run 'python -m benchmark.assessment' to analyze results"
echo ""
echo "📂 Results will be stored in:"
echo "   - benchmark/results/      (raw benchmark data)"
echo "   - benchmark/reports/      (assessment reports)"
echo "   - benchmark/visualizations/ (graphs and charts)"
echo ""
echo "Debug logs will be in benchmark/logs/"
