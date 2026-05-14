from typing import List, Tuple

from app.schemas.analytics import KSEBSlabBreakdown


KSEB_SLABS = [
    {"limit": 50, "rate": 3.25, "fixed": 40},
    {"limit": 100, "rate": 4.05, "fixed": 65},
    {"limit": 150, "rate": 5.10, "fixed": 85},
    {"limit": 200, "rate": 6.95, "fixed": 120},
    {"limit": 250, "rate": 8.20, "fixed": 120},
    {"limit": 300, "rate": 6.40, "fixed": 150},
    {"limit": 350, "rate": 7.25, "fixed": 175},
    {"limit": 400, "rate": 7.50, "fixed": 200},
    {"limit": 500, "rate": 7.90, "fixed": 230},
    {"limit": float("inf"), "rate": 8.80, "fixed": 260},
]
ELECTRICITY_DUTY_PCT = 0.10
METER_RENT = 15.0


def estimate_bill(total_units: float) -> Tuple[float, float, float, float, List[KSEBSlabBreakdown]]:
    remaining = max(total_units, 0)
    prev_limit = 0
    energy_charge = 0.0
    slabs: List[KSEBSlabBreakdown] = []
    fixed_charge = KSEB_SLABS[0]["fixed"]

    for slab in KSEB_SLABS:
        if remaining <= 0:
            break
        slab_size = slab["limit"] - prev_limit
        units_in_slab = min(remaining, slab_size)
        cost = round(units_in_slab * slab["rate"], 2)
        energy_charge += cost
        fixed_charge = slab["fixed"]

        label = (
            f"{prev_limit + 1}-{slab['limit']} units"
            if slab["limit"] != float("inf")
            else f"Above {prev_limit} units"
        )
        slabs.append(
            KSEBSlabBreakdown(
                slab_label=label,
                units=round(units_in_slab, 3),
                rate_per_unit=slab["rate"],
                slab_cost=cost,
            )
        )
        remaining -= units_in_slab
        prev_limit = slab["limit"]

    electricity_duty = round(energy_charge * ELECTRICITY_DUTY_PCT, 2)
    total_bill = round(fixed_charge + energy_charge + electricity_duty + METER_RENT, 2)
    return fixed_charge, round(energy_charge, 2), electricity_duty, total_bill, slabs


def project_monthly_units(total_kwh: float, sample_days: int, billing_days: int = 30) -> float:
    if sample_days <= 0:
        return 0.0
    return (total_kwh / sample_days) * billing_days
