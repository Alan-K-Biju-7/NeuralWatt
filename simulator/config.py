import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().with_name(".env")
load_dotenv(ENV_FILE)

# API
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
if not BASE_URL.endswith("/api/v1"):
    BASE_URL = f"{BASE_URL}/api/v1"

# Credentials
TOKEN = os.getenv("SIM_TOKEN", "")
EMAIL    = os.getenv("SIM_EMAIL",    "simulator@neuralwatt.app")
PASSWORD = os.getenv("SIM_PASSWORD", "Sim@12345")
FULL_NAME = os.getenv("SIM_FULL_NAME", "NeuralWatt Simulator")

# Auto-filled on first run
HOUSEHOLD_ID = os.getenv("HOUSEHOLD_ID", "")
DEVICE_ID    = os.getenv("DEVICE_ID",    "")

# Behaviour
INTERVAL_SECONDS  = int(os.getenv("INTERVAL_SECONDS", "30"))
SPIKE_PROBABILITY = float(os.getenv("SPIKE_PROBABILITY", "0.05"))
SPIKE_MULTIPLIER  = (2.5, 4.0)

# Device info
DEVICE_NAME = "Kerala Home Simulator"
DEVICE_TYPE = "other"
RATED_POWER_WATTS = 5000
LOCATION    = "Main Panel"
