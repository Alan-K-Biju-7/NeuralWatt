import os
from dotenv import load_dotenv

load_dotenv()

# API
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Credentials
EMAIL    = os.getenv("SIM_EMAIL",    "simulator@neuralwatt.local")
PASSWORD = os.getenv("SIM_PASSWORD", "Sim@12345")

# Auto-filled on first run
HOUSEHOLD_ID = os.getenv("HOUSEHOLD_ID", "")
DEVICE_ID    = os.getenv("DEVICE_ID",    "")

# Behaviour
INTERVAL_SECONDS  = 30
SPIKE_PROBABILITY = 0.05
SPIKE_MULTIPLIER  = (2.5, 4.0)

# Device info
DEVICE_NAME = "Kerala Home Simulator"
DEVICE_TYPE = "smart_meter"
LOCATION    = "Main Panel"
