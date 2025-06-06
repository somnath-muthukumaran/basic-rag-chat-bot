#!/bin/zsh
# setup.sh - Setup script for FastAPI server

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Upgrade pip, setuptools, wheel
pip install --upgrade pip setuptools wheel

# Install dependencies with trusted hosts workaround (for macOS SSL issues)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --index-url https://pypi.org/simple -r requirements.txt

# Export PYTHONPATH to include the server directory
export PYTHONPATH="${PYTHONPATH}:${PWD}"

echo "\nSetup complete! To activate the environment later, run:"
echo "  source venv/bin/activate"
echo "To start the server:"
echo "  ./run.py"
echo "source venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
