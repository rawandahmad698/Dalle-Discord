# Thank you! Mosquito.

import abc
import asyncio
import logging
from contextlib import suppress
from functools import wraps
from typing import (
    Any, Awaitable, Callable, Coroutine, Dict, Generator, List, MutableSet,
    NoReturn, Optional, Set, Tuple, TypeVar, Union,
)
from weakref import WeakSet

get_running_loop = getattr(asyncio, "get_running_loop", asyncio.get_event_loop)
log = logging.getLogger(__name__)
CloseCallbacksType = Callable[[], Union[Any, Coroutine]]


class TaskStore:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.tasks: MutableSet[asyncio.Task] = WeakSet()
        self.futures: MutableSet[asyncio.Future] = WeakSet()
        self.children: MutableSet[TaskStore] = WeakSet()
        self.close_callbacks: Set[CloseCallbacksType] = set()
        self.__loop = loop
        self.__closing: asyncio.Future = self.__loop.create_future()

    def get_child(self) -> "TaskStore":
        store = self.__class__(self.__loop)
        self.children.add(store)
        return store

    def add_close_callback(self, func: CloseCallbacksType) -> None:
        self.close_callbacks.add(func)

    def create_task(self, *args: Any, **kwargs: Any) -> asyncio.Task:
        task = self.__loop.create_task(*args, **kwargs)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.remove)
        return task

    def create_future(self) -> asyncio.Future:
        future = self.__loop.create_future()
        self.futures.add(future)
        future.add_done_callback(self.futures.remove)
        return future

    @property
    def is_closed(self) -> bool:
        return self.__closing.done()

    async def close(self, exc: Optional[Exception] = None) -> None:
        if self.__closing.done():
            return

        if exc is None:
            self.__closing.set_result(True)
        else:
            self.__closing.set_exception(exc)

        for future in self.futures:
            if future.done():
                continue

            future.set_exception(
                exc or asyncio.CancelledError("Object %r closed" % self),
            )

        tasks: List[Union[asyncio.Future, Coroutine]] = []

        for func in self.close_callbacks:
            try:
                result = func()
            except BaseException:
                log.exception("Error in close callback %r", func)
                continue

            if (
                    asyncio.iscoroutine(result) or
                    isinstance(result, asyncio.Future)
            ):
                tasks.append(result)

        for task in self.tasks:
            if task.done():
                continue

            task.cancel()
            tasks.append(task)

        for store in self.children:
            tasks.append(store.close())

        await asyncio.gather(*tasks, return_exceptions=True)


class AsyncClassMeta(abc.ABCMeta):
    def __new__(
            cls,
            clsname: str,
            bases: Tuple[type, ...],
            namespace: Dict[str, Any],
    ) -> "AsyncClassMeta":
        instance = super(AsyncClassMeta, cls).__new__(
            cls, clsname, bases, namespace,
        )

        if not asyncio.iscoroutinefunction(instance.__ainit__):  # type: ignore
            raise TypeError("__ainit__ must be coroutine")

        return instance


ArgsType = Any
KwargsType = Any


class AsyncClass(metaclass=AsyncClassMeta):
    __slots__ = ("_args", "_kwargs")
    _args: ArgsType
    _kwargs: KwargsType

    def __new__(cls, *args: Any, **kwargs: Any) -> "AsyncClass":
        self = super().__new__(cls)
        self._args = args
        self._kwargs = kwargs
        return self

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return get_running_loop()

    def __await__(self) -> Generator[None, Any, "AsyncClass"]:
        yield from self.__ainit__(*self._args, **self._kwargs).__await__()
        return self

    async def __ainit__(self, *args: Any, **kwargs: Any) -> NoReturn:
        pass


# noinspection PyAttributeOutsideInit
class AsyncObject(AsyncClass):
    def __init__(self, *args: ArgsType, **kwargs: KwargsType):
        self.__closed = False
        self._async_class_task_store: TaskStore

    @property
    def __tasks__(self) -> TaskStore:
        return self._async_class_task_store

    @property
    def is_closed(self) -> bool:
        return self.__closed

    def create_task(
            self, *args: ArgsType, **kwargs: KwargsType
    ) -> asyncio.Task:
        return self.__tasks__.create_task(*args, **kwargs)

    def create_future(self) -> asyncio.Future:
        return self.__tasks__.create_future()

    async def __adel__(self) -> None:
        pass

    def __init_subclass__(cls, **kwargs: KwargsType):
        if getattr(cls, "__await__") is not AsyncObject.__await__:
            raise TypeError("__await__ redeclaration is forbidden")

    def __await__(self) -> Generator[Any, None, "AsyncObject"]:
        if not hasattr(self, "_async_class_task_store"):
            self._async_class_task_store = TaskStore(self.loop)

        yield from self.create_task(
            self.__ainit__(*self._args, **self._kwargs),
        ).__await__()
        return self

    def __del__(self) -> None:
        if self.__closed:
            return

        with suppress(BaseException):
            self.loop.create_task(self.close())

    async def close(self, exc: Optional[Exception] = None) -> None:
        if self.__closed:
            return

        tasks: List[Union[asyncio.Future, Coroutine]] = []

        if hasattr(self, "_async_class_task_store"):
            tasks.append(self.__adel__())
            tasks.append(self.__tasks__.close(exc))
            self.__closed = True

        if not tasks:
            return

        await asyncio.gather(*tasks, return_exceptions=True)


T = TypeVar("T")


def task(
        func: Callable[..., Coroutine[Any, None, T]],
) -> Callable[..., Awaitable[T]]:
    @wraps(func)
    def wrap(
            self: AsyncObject,
            *args: ArgsType,
            **kwargs: KwargsType
    ) -> Awaitable[T]:
        # noinspection PyCallingNonCallable
        return self.create_task(func(self, *args, **kwargs))

    return wrap


def link(who: AsyncObject, where: AsyncObject) -> None:
    who._async_class_task_store = where.__tasks__.get_child()
    who.__tasks__.add_close_callback(who.close)


__all__ = (
    "AsyncClass",
    "AsyncObject",
    "CloseCallbacksType",
    "TaskStore",
    "link",
    "task",
)
