from __future__ import annotations

import argparse
import json
import math
import os
import re
import select
import sys
import termios
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any


READING_RE = re.compile(
    r"P1\s+"
    r"V:?(?P<voltage>[-+.\w]+)\s+"
    r"I:?(?P<current>[-+.\w]+)\s+"
    r"P:?(?P<power>[-+.\w]+)\s+"
    r"E:?(?P<energy>[-+.\w]+)\s+"
    r"F:?(?P<frequency>[-+.\w]+)\s+"
    r"PF:?(?P<power_factor>[-+.\w]+)"
)

BAUD_RATES = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
}


def finite_float(value: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def configure_serial(fd: int, baud: int) -> None:
    if baud not in BAUD_RATES:
        raise ValueError(f"Unsupported baud rate: {baud}")

    attrs = termios.tcgetattr(fd)
    attrs[0] = termios.IGNBRK
    attrs[1] = 0
    attrs[2] = termios.CLOCAL | termios.CREAD | termios.CS8
    attrs[3] = 0
    attrs[4] = BAUD_RATES[baud]
    attrs[5] = BAUD_RATES[baud]
    attrs[6][termios.VMIN] = 0
    attrs[6][termios.VTIME] = 10
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    termios.tcflush(fd, termios.TCIOFLUSH)


def parse_line(line: str) -> dict[str, float] | None:
    match = READING_RE.search(line)
    if not match:
        return None

    values = {key: finite_float(value) for key, value in match.groupdict().items()}
    if values["power"] is None:
        return None
    return {
        "power_w": round(values["power"] or 0.0, 2),
        "voltage_v": values["voltage"],
        "current_a": values["current"],
        "energy_kwh": values["energy"],
        "frequency_hz": values["frequency"],
        "power_factor": values["power_factor"],
        "source": "pzem_004t",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def post_reading(
    api_base: str,
    household_id: str,
    device_id: str,
    device_key: str,
    payload: dict[str, Any],
) -> None:
    url = (
        f"{api_base.rstrip('/')}/households/{household_id}"
        f"/devices/{device_id}/readings"
    )
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if device_key:
        headers["X-Device-Key"] = device_key
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status not in (200, 201):
            raise RuntimeError(f"Unexpected API status: {response.status}")


def bridge(args: argparse.Namespace) -> None:
    fd = os.open(args.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        configure_serial(fd, args.baud)
        print(f"Listening on {args.port} at {args.baud} baud")
        print(f"Posting to {args.api_base}")
        buffer = b""
        while True:
            readable, _, _ = select.select([fd], [], [], 1.0)
            if not readable:
                continue

            chunk = os.read(fd, 1024)
            if not chunk:
                time.sleep(0.1)
                continue
            buffer += chunk

            while b"\n" in buffer:
                raw, buffer = buffer.split(b"\n", 1)
                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                payload = parse_line(line)
                if not payload:
                    print(f"serial: {line}")
                    continue
                try:
                    post_reading(
                        args.api_base,
                        args.household_id,
                        args.device_id,
                        args.device_key,
                        payload,
                    )
                    print(
                        "sent",
                        f"{payload['power_w']:.2f} W",
                        f"V={payload.get('voltage_v')}",
                        f"I={payload.get('current_a')}",
                    )
                except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                    print(f"post failed: {exc}", file=sys.stderr)
    finally:
        os.close(fd)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bridge ESP32 Serial PZEM readings into the NeuralWatt API."
    )
    parser.add_argument("--port", default="/dev/cu.usbserial-0001")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--api-base", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--household-id", default="demo-household")
    parser.add_argument("--device-id", default="pzem-1")
    parser.add_argument("--device-key", default="dev-pzem-key")
    args = parser.parse_args()

    try:
        bridge(args)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
