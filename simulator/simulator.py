import time
import random
import logging
from datetime import datetime, timezone

import requests

import config
from patterns import get_watts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("simulator")

SESSION = requests.Session()
SESSION.headers.update({"Content-Type": "application/json"})

_token     = ""
_household = config.HOUSEHOLD_ID
_device    = config.DEVICE_ID


def _register():
    r = SESSION.post(f"{config.BASE_URL}/auth/register",
        json={"email": config.EMAIL, "password": config.PASSWORD})
    if r.status_code in (200, 201):
        log.info("✅ Simulator user registered")
        return True
    if r.status_code == 400 and "already" in r.text.lower():
        log.info("ℹ️  Simulator user already exists")
        return True
    log.error("❌ Register failed: %s", r.text)
    return False


def _login():
    global _token
    r = SESSION.post(f"{config.BASE_URL}/auth/login",
        json={"email": config.EMAIL, "password": config.PASSWORD})
    if r.status_code == 200:
        _token = r.json().get("access_token", "")
        SESSION.headers["Authorization"] = f"Bearer {_token}"
        log.info("🔑 Logged in")
        return True
    log.error("❌ Login failed: %s", r.text)
    return False


def _write_env(key, value):
    try:
        with open(".env", "r") as f:
            lines = f.readlines()
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
        with open(".env", "w") as f:
            f.writelines(lines)
    except Exception as e:
        log.warning("Could not update .env: %s", e)


def _ensure_household():
    global _household
    if _household:
        return True
    r = SESSION.post(f"{config.BASE_URL}/households", json={
        "name":     "Simulated Kerala Home",
        "location": "Thiruvananthapuram, Kerala",
        "members":  4,
    })
    if r.status_code in (200, 201):
        _household = r.json()["_id"]
        _write_env("HOUSEHOLD_ID", _household)
        log.info("🏠 Household created: %s", _household)
        return True
    log.error("❌ Household failed: %s", r.text)
    return False


def _ensure_device():
    global _device
    if _device:
        return True
    r = SESSION.post(
        f"{config.BASE_URL}/households/{_household}/devices", json={
        "name":     config.DEVICE_NAME,
        "type":     config.DEVICE_TYPE,
        "location": config.LOCATION,
    })
    if r.status_code in (200, 201):
        _device = r.json()["_id"]
        _write_env("DEVICE_ID", _device)
        log.info("📟 Device created: %s", _device)
        return True
    log.error("❌ Device failed: %s", r.text)
    return False


def _send_reading():
    hour  = datetime.now(timezone.utc).hour
    watts = get_watts(hour)

    if random.random() < config.SPIKE_PROBABILITY:
        watts = round(watts * random.uniform(*config.SPIKE_MULTIPLIER), 2)
        log.warning("⚡ SPIKE injected → %.1f W", watts)

    payload = {
        "watts":     watts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source":    "simulator",
    }
    r = SESSION.post(
        f"{config.BASE_URL}/households/{_household}/devices/{_device}/readings",
        json=payload,
    )
    if r.status_code in (200, 201):
        log.info("📤 Sent %.1f W  [hour=%02d]", watts, hour)
    elif r.status_code == 401:
        log.warning("🔑 Token expired — re-logging in")
        _login()
    else:
        log.error("❌ Send failed (%s): %s", r.status_code, r.text)


def main():
    log.info("🚀 NeuralWatt Simulator starting...")
    log.info("   API      : %s", config.BASE_URL)
    log.info("   Email    : %s", config.EMAIL)
    log.info("   Interval : %ds", config.INTERVAL_SECONDS)

    if not (_register() and _login() and _ensure_household() and _ensure_device()):
        log.critical("Bootstrap failed. Exiting.")
        return

    log.info("✅ Bootstrap complete — sending readings every %ds", config.INTERVAL_SECONDS)

    while True:
        try:
            _send_reading()
        except Exception as e:
            log.exception("Unexpected error: %s", e)
        time.sleep(config.INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
