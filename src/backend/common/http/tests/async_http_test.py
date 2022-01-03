
import pytest
import requests
from google.appengine.api import memcache
from google.appengine.api.memcache.memcache_stub import MemcacheServiceStub
from google.appengine.api.urlfetch_stub import _SetupSSL
from google.appengine.ext import testbed

from backend.common.futures import AwaitableRPC
from backend.common.http.urlfetch_adapter import URLFetchAdapter
from backend.common.http.urlfetch_session import URLFetchSession


pytestmark = pytest.mark.asyncio


async def co_get(keys):
    client = memcache.Client()
    return await AwaitableRPC(client.get_multi_async(keys))


async def co_set(mapping):
    client = memcache.Client()
    return await AwaitableRPC(client.set_multi_async(mapping))


async def test_memcache(memcache_stub) -> None:
    MemcacheServiceStub.THREADSAFE = True
    resp1 = await co_get(["foo", "bar"])
    assert resp1 == {}

    await co_set({"foo": "one", "bar": "two"})

    resp2 = await co_get(["foo", "bar"])
    assert resp2 == {"foo": "one", "bar": "two"}


@pytest.mark.skip
def test_urlfetch_adapter(gae_testbed: testbed.Testbed) -> None:
    gae_testbed.init_urlfetch_stub()
    _SetupSSL("/etc/ssl/certs/ca-bundle.crt")

    s = requests.Session()
    a = URLFetchAdapter()
    s.mount("http://", a)
    s.mount("https://", a)

    resp = s.get("http://www.thebluealliance.com/api/v3/status")
    assert resp.json() == {}


async def test_urlfetch_session(gae_testbed: testbed.Testbed) -> None:
    gae_testbed.init_urlfetch_stub()
    _SetupSSL("/etc/ssl/certs/ca-bundle.crt")

    s = URLFetchSession()
    resp = await s.get("http://www.thebluealliance.com/api/v3/status")
    assert resp.json() == {}
