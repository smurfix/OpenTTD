#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the+ GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without+ even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the+ GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Some utility functions
"""
from __future__ import annotations

import anyio
from contextlib import nullcontext
from operator import itemgetter
from ._util import capture
from heapq import heappush,heappop

test_stop = None  # from openttd.base. Circular import. Patched in later.

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Awaitable,Sequence

class _add_new_checker(type):
    def __instancecheck__(cls,obj):
        return type(obj) in (cls,cls._DERIV__Base)
    def __call__(cls,*a,**kw):
        if cls._DERIV__over_new:
            return cls._DERIV__Base(*a,**kw)
        return cls.__new__(cls,*a,**kw)
    def __repr__(self):
        return repr(self._DERIV__Base)
    def __str__(self):
        return str(self._DERIV__Base)
    def __getattr__(self, k):
        return getattr(self._DERIV__Base, k)


def extension_of(base: type) -> Callable[[type],type]:
    """
    Mostly-transparently extend a class or enum with additional methods.
    This is a shorthand for monkeypatching the base class.

    Usage::

        class Base(enums.Enum):
            A=1
            B=2
            C=3

        @extension_of(Base)
        class Deriv(_ID, int):
            def hello(self,x):
                assert isinstance(self,Base)
                return x+self.value

        x1 = Deriv(2)
        x2 = Deriv(x1)
        x3 = Base(2)
        assert x1 is x2
        assert x1 is x3
        assert x3.hello(42) == 44
    """
    def mangler(deriv: type):
        import _ttd
        import os
        if "PY_OTTD_STUB_GEN" in os.environ:
            return deriv
        for k in dir(deriv):
            if k.startswith("__") and hasattr(base,k):
                continue
            v = getattr(deriv,k)
            setattr(base,k,v)
        for k in ("__members__",):
            try:
                v = getattr(base,k)
            except AttributeError:
                pass
            else:
                try:
                    setattr(deriv,k,v)
                except AttributeError:
                    pass

        class DERIV(deriv,metaclass=_add_new_checker):
            __Base=base
            __over_new = "__new__" not in deriv.__dict__
        DERIV.__name__=deriv.__name__
        return DERIV
    return mangler

async def maybe_async(fn, *a, **kw):
    """
    This wrapper calls the supplied function, then waits for the result
    if it's asynchronous.

    This is useful if you need to call commands from the main thread:
    they might not return an awaitable on error.
    """
    res = fn(*a, **kw)
    if hasattr(res, "__await__"):
        res = await res
        return res

async def maybe_async_threaded(fn, *a, **kw):
    """
    This wrapper runs the supplied function in a subthread. If the result
    is an Awaitable, it waits for it.

    This is useful if you need to call user-supplied code and you don't
    know whether it's async or not.
    """
    # The capture/unwrap wrapper is required for Trio: returning an Awaitable
    # from a subthread smells like an async function call that ended up in
    # a thread, thus Trio raises an exception instead of returning it to us.
    def syn(fn,a,kw):
        from ._main import _async
        _async.set(False)
        return fn(*a,**kw)
    res = (await anyio.to_thread.run_sync(capture,syn,fn,a,kw)).unwrap()
    if hasattr(res,"__await__"):
        res = await res
    return res

def testmode_if(flag:bool):
    """
    This wrapper calls the supplied function in test mode if the flag is
    True.

    Usage::

        def do_something(estimate_only:bool):
            ...
            with testmode_if(estimate_only):
                build_road(...)

    """
    if flag:
        from openttd._main import test_mode
        return test_mode()
    else:
        return nullcontext()

class AsyncInit(type):
    """
    A metaclass that allows you to instantiate a class asynchronously.

    Usage::

        class A(metaclass=AsyncInit):
            async def __init__(self, n):
                print(f"{n=} - twiddling thumbs")
                await anyio.sleep(2)
                print("initialization finished")

        ...
        a_instance = await A()


    """
    async def __call__(cls, *args, **kwargs):
        instance = cls.__new__(cls, *args, **kwargs)
        if isinstance(instance, cls):
            await instance.__init__(*args, **kwargs)
        return instance


type T = Any

class PlusSet[T](set):
    """
    This class augments sets with a couple of operations that make working
    with them somewhat more convenient.

    ``set @ filter``, ``set @= filter``: apply the filter function to each member
    and delete those for which the filter returns `False`.

    Thus, ``PlusSet([1,2,3,4]) @ lambda x:x<3 == [1, 2]``.

    min, max: Find the member that minimizes / maximizes a given function.

    min_n, max_n: Ditto, but returns the N largest / smallest elements.
    """

    def filter(self, test: Callable[[T],bool]) -> set[T]:
        """
        Filter the list by a test function.

        The original is not modified: the result is a new list.

        This method is aliased to the `@` operator. Use `@=` if you want to
        filter in-place (i.e. remove the members that do not match).
        """
        res = set()
        for t in self:
            if test(t):
                res.add(t)
        return res

    __matmul__ = filter

    async def filter_a(self, test: Callable[[T],Awaitable[bool]]) -> set[T]:
        """
        Filter the list by an async test function.

        The original is not modified: the result is a new list.
        """
        res = set()
        for t in self:
            if await test(t):
                res.add(t)
        return self

    def __imatmul__(self, test: Callable[[T],bool]) -> set[T]:
        """
        Filter the list by a test function.

        Non-matching members are removed.
        """
        drop = []
        for t in self:
            if not test(t):
                drop.append(t)
        for t in drop:
            self.remove(t)
        return self

    async def filtered_a(self, test: Callable[[T],Awaitable[bool]]) -> set[T]:
        drop = []
        for t in self:
            if not await test(t):
                drop.append(t)
        for t in drop:
            self.remove(t)
        return self

    def min(self, key: Callable[[T], int|float]) -> T:
        "Return the smallest element, according to a key function"
        tt = iter(self)
        res = next(tt)
        val = key(res)
        for tile in tt:
            test_stop()
            if (v := key(tile)) < val:
                res = tile
                val = v
        return res

    def max(self, key: Callable[[T], int|float]) -> T:
        "Return the largest element, according to a key function"
        tt = iter(self)
        res = next(tt)
        val = key(res)
        for tile in tt:
            test_stop()
            if (v := key(tile)) > val:
                res = tile
                val = v
        return res

    def max_n(self, n:int, key: Callable[[T], int|float]) -> Sequence[T]:
        """
        Return the N largest elements, as selected by the function 'key'.

        The result is *not* sorted.
        """

        res = []
        for x in self:
            test_stop()
            heappush(res,(key(x),x))
            if len(res) > n:
                # too long: take the smallest element off
                heappop(res)
        return map(itemgetter(1), res)

    def min_n(self, n:int, key: Callable[[T], int|float]) -> Sequence[T]:
        """
        Return the smallest element, as selected by the function 'key'.

        The result is *not* sorted.
        """
        res = []
        for x in self:
            test_stop()
            heappush(res,(-key(x),x))
            if len(res) > n:
                # too long: take the largest element off
                heappop(res)
        return map(itemgetter(1), res)


    # async versions, if you need this in the main loop

    async def min_a(self, key: Callable[[T], Awaitable[int|float]]) -> T:
        """
        Return the smallest element, as selected by the function 'key'.

        This is an async function. The key function may be async
        but doesn't need to be; if it is, it *must* call 'anyio.sleep'
        (or some equivalent tat causes scheduling).
        """
        it = iter(self)
        res = next(it)
        val = key(res)

        if hasattr(val,__await__):
            async def adapt(res):
                return await res
        else:
            async def adapt(res):
                await anyio.sleep(0)
                return res

        for tile in it:
            if (v := (await adapt(key(tile)))) < val:
                res = tile
                val = v
        return res

    async def max_a(self, key: Callable[[T], Awaitable[int|float]]) -> T:
        """
        Return the largest element, as selected by the function 'key'.

        This is an async function. The key function may be async
        but doesn't need to be; if it is, it *must* call 'anyio.sleep'
        (or some equivalent tat causes scheduling).
        """
        it = iter(self)
        res = next(it)
        val = key(res)

        if hasattr(val,__await__):
            async def adapt(res):
                return await res
        else:
            async def adapt(res):
                await anyio.sleep(0)
                return res

        for tile in it:
            if (v := (await adapt(key(tile)))) > val:
                res = tile
                val = v
        return res

    async def max_na(self, n:int, key: Callable[[T], Awaitable[int|float]]) -> Sequence[T]:
        "Return the N largest elements, according to a key"

        res = []
        it = iter(self)
        x = next(it)
        val = key(t)
        if hasattr(val,__await__):
            async def adapt(res):
                return await res
        else:
            async def adapt(res):
                await anyio.sleep(0)
                return res
        res.append((val,x))

        for x in it:
            heappush(res,((await adapt(key(x))),x))
            if len(res) > n:
                # too long: take the smallest element off
                heappop(res)
        return map(itemgetter(1), res)

    async def min_na(self, n:int, key: Callable[[T], Awaitable[int|float]]) -> Sequence[T]:
        "Return the N largest elements, according to a key"

        res = []
        it = iter(self)
        x = next(it)
        val = key(t)
        if hasattr(val,__await__):
            async def adapt(res):
                return await res
        else:
            async def adapt(res):
                await anyio.sleep(0)
                return res
        res.append((-val,x))

        for x in it:
            heappush(res,(-(await adapt(key(x))),x))
            if len(res) > n:
                # too long: take the smallest element off
                heappop(res)
        return map(itemgetter(1), res)
