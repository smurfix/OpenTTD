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
from functools import partial
from contextvars import ContextVar
from concurrent.futures import CancelledError

import openttd
from openttd._main import _storage, _main, estimating, VEvent, test_mode

__all__ = ["GameScript","AIScript"]

# Set to a cancel-test procedure.
def _err():
    raise CancelledError

_STOP = ContextVar("_STOP", default=_err)

def test_stop():
    _STOP.get()()

class _HLT:
    res=None
    halt=False
    def __init__(self):
        self.evt=anyio.Event()

    def STOP(self):
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

    Scripts may not block!
    """
    __setup_called = False
    __storage: Storage
    __id: int
    __company: Company
    __kw: dict[str,int|float|str]
    __state: Any
    __stopped: bool = False

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

    # TODO typing
    async def subthread(self, proc:Callable, *a, **kw) -> Awaitable[Any]:
        """
        Start a thread, and wait for the result.

        The thread can read OpenTTD data. It runs synchronously.
        Test mode is enabled.

        Your procedure *MUST* periodically call 'test_stop()'.
        This call will raise a `CancelledError` exception if your thread
        should exit. *DO NOT* ignore it.
        """

        hlt = _HLT()

        def _call2(hlt,proc,a,k):
            _STOP.set(hlt.STOP)
            estimating.set(True)
            return proc(*a,**kw)

        async def _call(hlt,proc,a,kw):
            try:
                hlt.res = await anyio.to_thread.run_sync(_call2,hlt,proc,a,kw, abandon_on_cancel=True)
            except* CancelledError:
                pass
            hlt.evt.set()

        async with anyio.create_task_group() as tg:
            try:
                tg.start_soon(_call,hlt,proc,a,kw)
                await hlt.evt.wait()
                return hlt.res
            except BaseException:
                hlt.stop=True
                raise

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
        import _ttd
        evt = VEvent()
        self.__storage = st = _ttd.object.Storage(self.__company)
        _storage.set(st)
        _STOP.set(self._test_stop)
        task = _main.get()

        async with anyio.create_task_group() as self.taskgroup:
            if self.__state is None:
                res = await self.setup(**self.__kw)
            else:
                res = await self.restore(self.__state)
            if not self.__setup_called:
                raise RuntimeError("You forgot to `await super().setup()`.")

            evt.value = res
            task_status.started(evt)
            try:
                evt.value = await self.main()
            except Exception as exc:
                self.log.exception("Script Error")
                self.print(f"DEAD: {exc}")
                evt.value = exc
            except BaseException as exc:
                self.print(f"DEAD: {exc}")
                evt.value = exc
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

    async def setup(self):
        """
        Override this to set up your script.
        All script arguments are passed to this method, as keywords.

        Don't forget to call `await super().setup()`.
        """
        self.__setup_called = True

    async def restore(self):
        """
        Override this to restore your script's status / savegame data.
        Called instead of `setup`.

        Don't forget to call `await super().setup()`.
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


class GameScript(BaseScript):
    """
    This class checks the company attribute and raises an error if it was
    called as an AI.

    NB: Game scripts run in all modes. You might
    """

    async def setup(self, **kw):
        if self.company != openttd.company.ID.DEITY:
            raise RuntimeError("This is a game script. It doesn't work as an AI.")
        await super().setup(*kw)

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
    async def setup(self, **kw):
        if self.company == openttd.company.ID.DEITY:
            raise RuntimeError("This is an AI script. It doesn't work as a game script.")
        await super().setup(*kw)

