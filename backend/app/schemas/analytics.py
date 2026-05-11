from pydantic import BaseModel
from typing import List, Optional


class DailyUsagePoint(BaseModel):
    date: str               # "2026-05-11"
    kwh: float              # total energy consumed that day
    avg_watts: float        # average power draw
    peak_watts: float       # max recorded reading
    reading_count: int      # number of readings that day


class DailyUsageResponse(BaseModel):
    device_id: str
    unit: str = "kWh"
    days: List[DailyUsagePoint]
    total_kwh: float
    from_date: str
    to_date: str


class HourlyUsagePoint(BaseModel):
    hour: int               # 0-23
    avg_watts: float
    peak_watts: float
    reading_count: int


class HourlyUsageResponse(BaseModel):
    device_id: str
    hours: List[HourlyUsagePoint]
    peak_hour: int
    peak_hour_avg_watts: float


class UsageReportResponse(BaseModel):
    device_id: str
    household_id: str
    period: str             # "weekly" | "monthly"
    from_date: str
    to_date: str
    total_kwh: float
    avg_daily_kwh: float
    peak_day: str
    peak_day_kwh: float
    low_day: str
    low_day_kwh: float
    anomaly_count: int
    days: List[DailyUsagePoint]


class KSEBSlabBreakdown(BaseModel):
    slab_label: str         # e.g. "0–50 units"
    units: float            # kWh consumed in this slab
    rate_per_unit: float    # ₹ per kWh
    slab_cost: float        # units × rate


class CostEstimateResponse(BaseModel):
    device_id: str
    from_date: str
    to_date: str
    total_kwh: float
    tariff_type: str = "KSEB Domestic LT-1 (Telescopic)"
    currency: str = "INR"
    fixed_charge: float
    energy_charge: float
    electricity_duty_pct: float = 10.0     # 10% ED on energy charge
    electricity_duty: float
    meter_rent: float = 15.0               # standard single-phase meter rent
    total_bill: float
    slab_breakdown: List[KSEBSlabBreakdown]
    daily_breakdown: List[dict]            # [{date, kwh, approx_cost}]
