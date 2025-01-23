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

import openttd
from openttd._main import _storage, _main

__all__ = ["GameScript","AIScript"]


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

    def __init__(self, id, company, state=None, /, **kw):
        self.__id = id
        self.__company = company
        self.__kw = kw
        self.__state = state

        self.log = logging.getLogger(self.__module__)

        if self._run.__func__ is not BaseScript._run:
            raise RuntimeError("Don't even think of overriding '_run'!")

    @property
    def company(self):
        """Returns the company this script runs as."""
        return self.__company

    def print(self, *a, **kw):
        """
        like Python's, but goes to the OpenTTD console.
        """
        task = _main.get()
        task.print(f"{self.__id}:", *a, **kw)

    def pprint(self, *a, **kw):
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

    async def _run(self, *, task_status):
        import _ttd
        self.__storage = st = _ttd.object.Storage(self.__company)
        _storage.set(st)
        task = _main.get()

        async with anyio.create_task_group() as self.taskgroup:
            if self.__state is None:
                res = await self.setup(**self.__kw)
            else:
                res = await self.restore(self.__state)
            if not self.__setup_called:
                raise RuntimeError("You forgot to `await super().setup()`.")

            task_status.started(res)
            if res is None:
                self.print("Script started.")
            else:
                self.print(f"Script started: {res}")
            try:
                await self.main()
            except Exception as exc:
                self.log.exception("Script Error")
                self.print(f"DEAD: {exc}")
            except BaseException as exc:
                self.print(f"DEAD: {exc}")
                raise
            else:
                self.print("Script terminated.")
            finally:
                self.stop()
                task.script_done(self.__id)

    def stop(self):
        """
        Stop this script (by cancelling its taskgroup).

        You may self-call this method.
        """
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

