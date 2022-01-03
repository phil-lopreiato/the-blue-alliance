import logging
import types
from typing import Awaitable, Any, Generic, Generator, Optional, TypeVar, overload

from google.appengine.api import apiproxy_rpc
from google.appengine.api.apiproxy_stub_map import UserRPC
from google.appengine.ext import ndb


T = TypeVar("T")


class AwaitableRPC(Awaitable):
    def __init__(self, rpc: UserRPC) -> None:
        self.rpc = rpc

    def __await__(self) -> Generator[Any, None, Any]:
        while self.rpc.state == apiproxy_rpc.RPC.RUNNING:
            yield
        if self.rpc.state == apiproxy_rpc.RPC.RUNNING:
            raise RuntimeError("await wasn't used with future!")
        return self._transform_response(self.rpc.get_result())

    def _transform_response(self, resp):
        return resp


class TypedFuture(ndb.Future, Generic[T]):
    def done(self) -> bool:
        return super().done()

    def wait(self) -> None:
        super().wait()

    def check_success(self) -> None:
        super().check_success()

    def set_result(self, result: T) -> None:
        super().set_result(result)

    def set_exception(self, exc: Exception, tb=None) -> None:
        super().set_exception(exc, tb)

    def get_result(self) -> T:
        return super().get_result()

    def get_exception(self) -> Exception:
        return super().get_exception()

    def get_traceback(self) -> Optional[types.TracebackType]:
        return super().get_traceback()


class AwaitableFuture(Generic[T], Awaitable[T]):

    @overload
    def __init__(self, future: TypedFuture[T]) -> None:
        ...

    @overload
    def __init__(self, future: ndb.Future) -> None:
        ...

    def __init__(self, future) -> None:
        self.future = future

    def __await__(self) -> Generator[Any, None, T]:
        ev = ndb.eventloop.get_event_loop()
        while not self.future.done():
            if not ev.run1():
                logging.info('Deadlock in %s', self)
                raise RuntimeError('Deadlock waiting for %s' % self)
            yield
        if not self.future.done():
            raise RuntimeError("await wasn't used with future!")
        return self.future.get_result()


class InstantFuture(TypedFuture[T], Generic[T]):
    def __init__(self, result: T):
        super().__init__()
        self.set_result(result)


class FailedFuture(TypedFuture[T], Generic[T]):
    def __init__(self, exception: Exception):
        super().__init__()
        self.set_exception(exception)
