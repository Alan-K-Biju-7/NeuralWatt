import time
import random
import logging
from datetime import datetime, timezone
from pathlib import Path

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


def _error_detail(response):
    try:
        return response.json().get("detail", response.text)
    except ValueError:
        return response.text


def _register():
    if config.TOKEN:
        log.info("🔑 Using configured API token")
        return True

    r = SESSION.post(f"{config.BASE_URL}/auth/register",
        json={
            "email": config.EMAIL,
            "password": config.PASSWORD,
            "full_name": config.FULL_NAME,
        })
    if r.status_code in (200, 201):
        log.info("✅ Simulator user registered")
        return True
    if r.status_code in (400, 409) and "already" in r.text.lower():
        log.info("ℹ️  Simulator user already exists")
        return True
    log.error("❌ Register failed: %s", _error_detail(r))
    return False


def _login():
    global _token
    if config.TOKEN:
        _token = config.TOKEN
        SESSION.headers["Authorization"] = f"Bearer {_token}"
        return True

    r = SESSION.post(f"{config.BASE_URL}/auth/login",
        json={"email": config.EMAIL, "password": config.PASSWORD})
    if r.status_code == 200:
        _token = r.json().get("access_token", "")
        SESSION.headers["Authorization"] = f"Bearer {_token}"
        log.info("🔑 Logged in")
        return True
    log.error("❌ Login failed: %s", _error_detail(r))
    return False


def _write_env(key, value):
    try:
        env_path = Path(config.ENV_FILE)
        if env_path.exists():
            lines = env_path.read_text().splitlines(keepends=True)
        else:
            lines = []
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
        env_path.write_text("".join(lines))
    except Exception as e:
        log.warning("Could not update .env: %s", e)


def _load_existing_household():
    global _household
    r = SESSION.get(f"{config.BASE_URL}/households/me")
    if r.status_code == 200:
        household_id = r.json()["id"]
        if _household and _household != household_id:
            log.warning(
                "Configured household %s does not belong to this token; using %s",
                _household,
                household_id,
            )
        _household = household_id
        _write_env("HOUSEHOLD_ID", _household)
        log.info("🏠 Using existing household: %s", _household)
        return True
    return False


def _ensure_household():
    global _household
    if _household and _load_existing_household():
        return True
    if _load_existing_household():
        return True
    r = SESSION.post(f"{config.BASE_URL}/households", json={
        "name":          "Simulated Kerala Home",
        "address":       "Thiruvananthapuram, Kerala",
        "num_occupants": 4,
    })
    if r.status_code in (200, 201):
        _household = r.json()["id"]
        _write_env("HOUSEHOLD_ID", _household)
        log.info("🏠 Household created: %s", _household)
        return True
    if r.status_code == 409 and _load_existing_household():
        return True
    log.error("❌ Household failed: %s", _error_detail(r))
    return False


def _load_existing_device():
    global _device
    if not _household:
        return False
    r = SESSION.get(f"{config.BASE_URL}/households/{_household}/devices")
    if r.status_code != 200:
        return False

    devices = r.json()
    if _device and any(device["id"] == _device for device in devices):
        log.info("📟 Using configured device: %s", _device)
        return True

    for device in devices:
        if device["name"] == config.DEVICE_NAME:
            _device = device["id"]
            _write_env("DEVICE_ID", _device)
            log.info("📟 Using existing device: %s", _device)
            return True
    return False


def _ensure_device():
    global _device
    if _load_existing_device():
        return True
    r = SESSION.post(
        f"{config.BASE_URL}/households/{_household}/devices", json={
        "name":              config.DEVICE_NAME,
        "device_type":       config.DEVICE_TYPE,
        "rated_power_watts": config.RATED_POWER_WATTS,
        "location":          config.LOCATION,
    })
    if r.status_code in (200, 201):
        _device = r.json()["id"]
        _write_env("DEVICE_ID", _device)
        log.info("📟 Device created: %s", _device)
        return True
    if r.status_code == 409 and _load_existing_device():
        return True
    log.error("❌ Device failed: %s", _error_detail(r))
    return False


def _send_reading():
    global _household, _device

    hour  = datetime.now(timezone.utc).hour
    watts = get_watts(hour)

    if random.random() < config.SPIKE_PROBABILITY:
        watts = round(watts * random.uniform(*config.SPIKE_MULTIPLIER), 2)
        log.warning("⚡ SPIKE injected → %.1f W", watts)

    payload = {
        "watts":     watts,
        "voltage":   round(random.uniform(218.0, 242.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload["current"] = round(payload["watts"] / payload["voltage"], 3)
    r = SESSION.post(
        f"{config.BASE_URL}/households/{_household}/devices/{_device}/readings",
        json=payload,
    )
    if r.status_code in (200, 201):
        log.info("📤 Sent %.1f W  [hour=%02d]", watts, hour)
    elif r.status_code == 401:
        log.warning("🔑 Token expired — re-logging in")
        _login()
    elif r.status_code in (403, 404):
        log.warning("📟 Stored household/device is stale or unauthorized — refreshing bootstrap")
        _household = ""
        _device = ""
        if _ensure_household() and _ensure_device():
            log.info("Bootstrap refreshed")
    else:
        log.error("❌ Send failed (%s): %s", r.status_code, _error_detail(r))


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
