import pytest
from google.appengine.ext import ndb
from backend.common.consts.event_type import EventType

from backend.common.futures import AwaitableFuture
from backend.common.models.event import Event

pytestmark = pytest.mark.asyncio


async def test_fetch_model(ndb_stub) -> None:
    Event(
        id="2020test",
        year=2020,
        event_short="test",
        event_type_enum=EventType.REGIONAL,
        name="Test Event",
    ).put()

    e = await AwaitableFuture(Event.get_by_id_async("2020test"))
    assert e is not None
    assert e.name == "Test Event"
