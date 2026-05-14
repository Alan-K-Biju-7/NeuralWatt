import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.core.dependencies import verify_reading_ingest_auth


class FakeCollection:
    def __init__(self, document):
        self.document = document
        self.updated = None

    async def find_one(self, query):
        if query.get("_id") == self.document["_id"]:
            return self.document
        return None

    async def update_one(self, query, update):
        self.updated = (query, update)


class FakeDb:
    def __init__(self, household):
        self.households = FakeCollection(household)


@pytest.mark.asyncio
async def test_verify_reading_ingest_auth_accepts_device_key():
    household_id = ObjectId()
    device_id = ObjectId()
    db = FakeDb(
        {
            "_id": household_id,
            "owner_id": "user-1",
            "name": "Demo Home",
            "devices": [
                {
                    "_id": device_id,
                    "name": "Main Meter",
                    "device_type": "other",
                    "rated_power_watts": 5000,
                    "device_key": "secret-key",
                }
            ],
        }
    )

    principal = await verify_reading_ingest_auth(
        str(household_id),
        str(device_id),
        x_device_key="secret-key",
        user_id=None,
        db=db,
    )

    assert principal.auth_type == "device_key"
    assert principal.device_id == str(device_id)


@pytest.mark.asyncio
async def test_verify_reading_ingest_auth_rejects_invalid_device_key():
    household_id = ObjectId()
    device_id = ObjectId()
    db = FakeDb(
        {
            "_id": household_id,
            "owner_id": "user-1",
            "name": "Demo Home",
            "devices": [
                {
                    "_id": device_id,
                    "name": "Main Meter",
                    "device_type": "other",
                    "rated_power_watts": 5000,
                    "device_key": "secret-key",
                }
            ],
        }
    )

    with pytest.raises(HTTPException) as error:
        await verify_reading_ingest_auth(
            str(household_id),
            str(device_id),
            x_device_key="wrong",
            user_id=None,
            db=db,
        )

    assert error.value.status_code == 401
