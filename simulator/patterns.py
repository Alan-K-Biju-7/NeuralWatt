import random

# (base_watts, noise_range) for each hour of the day
HOUR_PROFILES = {
    0:  (140, 20),   # deep night — fridge only
    1:  (130, 15),
    2:  (125, 15),
    3:  (120, 10),
    4:  (125, 15),
    5:  (200, 50),   # early rise — lights, phone charging
    6:  (380, 80),   # morning — fans, TV on
    7:  (950, 200),  # peak — water heater + pump
    8:  (1100, 250), # peak — water heater still running
    9:  (500, 100),  # settling — heater off, AC on low
    10: (420, 80),
    11: (380, 70),
    12: (340, 60),   # midday low
    13: (310, 50),
    14: (290, 50),   # afternoon low — most people out
    15: (320, 60),
    16: (480, 100),  # evening ramp — cooking starts
    17: (650, 120),
    18: (1100, 200), # peak — AC, cooking, TV
    19: (1400, 300), # biggest peak — full house active
    20: (1200, 250),
    21: (900, 200),  # wind-down
    22: (600, 150),
    23: (350, 80),
}


def get_watts(hour: int) -> float:
    """Return realistic watt reading for the given hour with natural noise."""
    base, noise = HOUR_PROFILES.get(hour, (300, 50))
    return round(max(80.0, base + random.uniform(-noise, noise)), 2)
