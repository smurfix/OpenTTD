#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module implements basic modular scripting support.
"""

from __future__ import annotations

import anyio
import logging
import threading
from contextvars import ContextVar
from contextlib import contextmanager
from concurrent.futures import CancelledError

import openttd
from ._main import _async, _storage, _main, estimating, VEvent, test_mode
from .util import maybe_async_threaded

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import ClassVar


__all__ = ["GameScript","AIScript"]

# Set to a cancel-test procedure.
def _err():
    raise CancelledError

SELF = ContextVar("SELF")
_STOP = ContextVar("_STOP", default=_err)

def test_stop():
    """
    Test whether your code should stop.

    If so, it raises a cancellation error.
    """
    _STOP.get()()

def sleep(ticks:int):
    SELF.get().sleep(ticks)

class HLT:
    """
    This object encapsulates a stoppable subthread and its result.
    """
    res=None
    halt=None
    def __init__(self):
        self.evt=anyio.Event()
        self.lock=threading.Lock()  # protects "halt"

    def wait(self):
        """
        Wait for the subthread to finish and return its result.

        If it raised an exception, that exception will be re-raised.
        """
        anyio.from_task.run(self.evt.wait)
        if isinstance(self.res, Exception):
            # this includes CancelledError
            raise self.res
        else:
            return self.res

    def stop(self):
        """
        Stop the subthread. (Or rather, ask it to stop.)
        """
        self.halt = True

    def _STOP(self):
        "this method is added to the `_STOP` contextvar"
        if self.halt:
            raise CancelledError


class BaseScript:
    """
    This is the base class for scripts interfacing with OpenTTD.

    You need to override "main" with your code.

    You may override the "setup" method. It gets the user's key/value arguments
    as input.

    Pre-defined attributes:
        * log: a `logging.Logger` instance you can use.
        * company: your company ID, or `openttd.company.ID.DEITY` for game scripts.
        * taskgroup: an `anyio.abc.TaskGroup` you can use to run subtasks


    Inheriting from `GameScript` or `AIScript` instead of `BaseScript`
    checks the company attribute and raises an error if the type is wrong.

    Scripts typically run in a subthread. They *must* periodically call
    either ``test_stop()``, ``sleep(game_ticks:int)``, or ``anyio.from_thread.*``.

    If you want more control, you can designate your script as
    asynchronous, simply by using "async main". If you do this,
    you're responsible for running everything that could possibly block in
    a subthread.
    """
    __setup_called = False
    __storage: Storage
    __id: int
    __company: Company
    __kw: dict[str,int|float|str]
    __state: Any
    __stopped: bool = False

    ATTRS:ClassVar[list[tuple[str,Any]]]=()  # (var,default), tuples

    def __init__(self, id, company, state=None, /, **kw):
        self.__id = id
        self.__company = company
        self.__kw = kw
        self.__state = state

        self.log = logging.getLogger(self.__module__)

        if self._run.__func__ is not BaseScript._run:
            raise RuntimeError("Don't even think of overriding '_run'!")

    test_stop = staticmethod(test_stop)
    test_mode = staticmethod(test_mode)

    @property
    def company(self):
        """Returns the company this script runs as."""
        return self.__company

    def sleep(self, ticks):
        """
        """
        if _async.get():
            return self._sleep(ticks)
        else:
            anyio.from_thread.run(self._sleep,ticks)

    async def _sleep(self, ticks):
        await _main.get().tick_wait(ticks)

    # TODO typing
    def subthread(self, proc:Callable, *a, **kw):
        """
        Start a thread.

        The thread can read OpenTTD data. It runs synchronously.
        Test mode is enabled.

        Your procedure *MUST* periodically call 'test_stop()'.
        This call will raise a `CancelledError` exception if your thread
        should exit. *DO NOT* ignore it.

        In sync mode, this method returns a `HLT` object.

        In async mode, awaiting this returns the subthread's result. You
        can stop the task the usual way (i.e. wrap the call to this method
        in an `anyio.CancelScope` and cancel that).
        """
        def _call2(hlt,proc,a,k):
            _STOP.set(hlt._STOP)
            _async.set(False)
            estimating.set(False)
            with hlt.lock:
                if hlt.halt is not None:
                    return
                hlt.halt=False
            return proc(*a,**kw)

        async def _call(hlt,proc,a,kw):
            try:
                hlt.res = await anyio.to_thread.run_sync(_call2,hlt,proc,a,kw, abandon_on_cancel=False)
            except* CancelledError:
                pass
            finally:
                hlt.halt=True
                hlt.evt.set()

        hlt = HLT()

        if _async.get():
            return self._subthread(_call,hlt,proc,a,kw)
        else:
            return anyio.from_thread.run_sync(self.taskgroup.start_soon,_call,hlt,proc,a,kw)

    async def _subthread(self, _call,hlt,proc,a,kw) -> Awaitable[Any]:
        "Encapsulate a subthread so it's cancelled on error."
        async with anyio.create_task_group() as tg:
            try:
                tg.start_soon(_call,hlt,proc,a,kw)
                await hlt.evt.wait()
            except BaseException:  # we got cancelled
                with hlt.lock:
                    if hlt.halt is None:
                        # didn't yet start, so set the event here.
                        hlt.evt.set()
                    hlt.halt=True
                    # otherwise _call2 is running, so _call will set the event.

                # In any case, we wait a bit for the thread to end
                with anyio.move_on_after(0.2,shield=True):
                    await hlt.evt.wait()
                    raise
                # ... and if it didn't, complain and wait somewhat longer
                self.log.error(f"Thread {proc} was asked to terminate but didn't")
                with anyio.move_on_after(1.5,shield=True):
                    await hlt.evt.wait()
                raise

            return hlt.res

    def print(self, *a, **kw) -> None:
        """
        like Python's, but goes to the OpenTTD console.
        """
        task = _main.get()
        task.print(f"{self.__id}:", *a, **kw)

    def pprint(self, *a, **kw) -> None:
        """
        pretty-print an object.
        """
        task = _main.get()
        task.pprint(*a, **kw)

    def get_info(self) -> str:
        """
        Returns a one-line status of this script.

        You should override this.
        """
        return f"(no info for {type(self)})"

    def dump(self) -> str:
        """
        Returns the detailed status of this script, as a Python data
        structure, usable for debugging.

        You should override this.
        """
        return []

    def get_state(self) -> str:
        """
        Returns a detailed state for this script.

        This state should be useable for restarting.

        You should override this.
        """
        return {}

    def _test_stop(self) -> bool:
        """
        Returns True if this script should stop.

        You should never call this. In async context, stopping is
        accomplished by getting cancelled. A subthread redirects _STOP to
        checking its HLT instead.
        """
        raise RuntimeError("You're async context. Run sync things in a thread!")


    async def _run(self, *, task_status):
        """
        The controlling task for this script, started from the main loop.

        Don't override this.
        """
        import _ttd
        evt = VEvent()
        self.__storage = st = _ttd.object.Storage(self.__company)
        _storage.set(st)
        _STOP.set(self._test_stop)
        SELF.set(self)

        task = _main.get()

        async with anyio.create_task_group() as self.taskgroup:
            try:
                if self.__state is None:
                    res = await maybe_async_threaded(self.setup, **self.__kw)
                else:
                    res = await maybe_async_threaded(self.restore,self.__state)
            except Exception as exc:
                self.log.exception("Script Setup Error")
                self.print(f"DEAD: {exc}")
                evt.value = exc
                task_status.started(evt)
                evt.event.set()
                return
            except BaseException as exc:
                self.print(f"DEAD: {exc}")
                evt.value = exc
                evt.event.set()
                raise

            if not self.__setup_called:
                raise RuntimeError("You forgot to call `super().setup()`.")

            evt.value = res
            task_status.started(evt)
            try:
                await maybe_async_threaded(self.main)
                self.taskgroup.cancel_scope.cancel()
            except Exception as exc:
                self.log.exception("Script Error")
                self.print(f"DEAD: {exc}")
                evt.value = exc
            except BaseException as exc:
                self.print(f"DEAD: {exc}")
                evt.value = CancelledError()
                raise
            else:
                self.print("Script terminated.")
            finally:
                self.stop()
                task.script_done(self.__id)
                evt.event.set()

    def stop(self):
        """
        Stop this script (by cancelling its taskgroup).

        You may self-call this method.
        """
        self.__stopped = True
        self.taskgroup.cancel_scope.cancel()

    def setup(self, **kw):
        """
        Override this to set up your script.
        All script arguments are passed to this method, as keywords.

        The default implementation assigns all attributes that are declared
        in ATTRS to the class, and refuses to add any that are not.

        Don't forget to call this, via `super().setup()`.
        """
        setup = {}
        for cls in self.__class__.__mro__:
            attr = cls.__dict__.get('ATTRS',())
            for k,v,*typ in setup:
                if k in setup:
                    continue
                if not typ:
                    typ = type(v)
                setup[k] = (v,typ)

        for k,v in kw.items():
            typ = setup[k][1]
            if not isinstance(v,typ):
                raise ValueError(f"The value of {k} must be {typ}, not {v !r}")
            setup[k] = v,

        for k,v in setup.items():
            setattr(self,k,v[0])

        self.__setup_called = True


    def save(self):
        """
        Override this to save your script's status / savegame data.

        Not yet used. TODO.
        """
        raise NotImplementedError

    def restore(self):
        """
        Override this to restore your script's status / savegame data.
        Called instead of `setup`. May be async.

        You still need to call `super().setup()`.
        """
        raise NotImplementedError

    async def main(self):
        """
        Override this to run your script.

        This method must not block.
        """
        raise NotImplementedError("You need to implement a 'main' method!")

    @property
    def pause_state(self) -> PauseState:
        return _main.pause_state

    def set_pause_state(self, mode: PauseState):
        """
        Game paused state change notification.

        You might want to override this.
        """
        pass

    def set_game_mode(self, mode: GameMode):
        """
        Game mode change notification.

        You might want to override this.
        """
        pass


class GameScript(BaseScript):
    """
    This class checks the company attribute and raises an error if it was
    called as an AI.

    NB: Game scripts run in all modes. You might
    """

    def setup(self, **kw):
        if self.company != openttd.company.ID.DEITY:
            raise RuntimeError("This is a game script. It doesn't work as an AI.")
        return super().setup(**kw)

    @property
    def game_mode(self) -> GameMode:
        return _main.game_mode

    def set_game_mode(self, mode: GameMode):
        """
        Game mode change notification.

        You might want to override this.
        """
        pass

class AIScript(BaseScript):
    """
    This class checks the company attribute and raises an error if it was
    called as a game script.
    """
    def setup(self, **kw):
        if self.company == openttd.company.ID.DEITY:
            raise RuntimeError("This is an AI script. It doesn't work as a game script.")
        return super().setup(*kw)

