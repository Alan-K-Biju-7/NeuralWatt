from app.services.tariff import estimate_bill, project_monthly_units


def test_estimate_bill_uses_kseb_slabs():
    fixed, energy, duty, total, slabs = estimate_bill(120)

    assert fixed == 85
    assert energy == 467.0
    assert duty == 46.7
    assert total == 613.7
    assert [slab.units for slab in slabs] == [50, 50, 20]


def test_project_monthly_units_handles_empty_samples():
    assert project_monthly_units(12, 0) == 0.0
    assert project_monthly_units(15, 5) == 90
