#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
OpenTTD's Python main loop.
"""
from __future__ import annotations

import openttd
import anyio
import traceback
import sys
import warnings
from functools import partial
from attrs import define,field
from contextvars import ContextVar
from importlib import import_module

import logging


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable

    class Command:
        pass
    class Tile:
        pass
    class CommandResult:
        pass

logger = logging.getLogger("OpenTTD")
log = logger.debug

_main = ContextVar("_main")
_storage = ContextVar("_storage")


@define(hash=True,eq=True)
class CmdR:
    cmd:Command
    p1:int
    p2:int
    p3:int
    tile:Tile


@define
class VEvent:
    """
    A rather primitive event-with-a-value type.

    There is no error/cancellation handling.
    """
    value: Any = None
    event: anyio.Event = field(factory=anyio.Event)


class Main:
    """
    The central control object.
    """
    _tg: anyio.abc.TaskGroup
    _replies:dict[CmdR, anyio.Event|CmdCost]

    def __init__(self):
        self._replies = {}

    async def _ttd_reader(self, queue, *, task_status):
        """
        Asynchronously read messages from OpenTTD.
        """
        def _read_queue():
            t = openttd.internal.task

            gen = t.wait(0)

            anyio.from_thread.run_sync(task_status.started, gen)
            while True:
                while True:
                    msg = t.recv()
                    if msg is None:
                        break
                    if isinstance(msg, openttd.internal.msg.Stop):
                        return

                    anyio.from_thread.run(queue.send,msg)
                gen = t.wait(gen)


        async def _run_thread():
            try:
                await anyio.to_thread.run_sync(_read_queue, abandon_on_cancel=True)
            finally:
                openttd.internal.task.stop()  # assuming there was an exception
                self._tg.cancel_scope.cancel()  # assuming we're told to shut down

        async with anyio.create_task_group() as tg:
            tg.start_soon(_run_thread)
            try:
                await anyio.sleep_forever()
            finally:
                openttd.internal.task.stop()  # assuming there was an exception

    async def _process(self, q):
        async for msg in q:
            try:
                res = msg.work(self)
                if hasattr(res,"__await__"):
                    await res
            except Exception:
                logger.exception("Error processing %r", msg)

    async def handle_command(self, msg):
        args = msg.args
        try:
            cmd = getattr(self, f"cmd_{args[0]}")
        except AttributeError:
            self.print(f"Command {args[0]} unknown. Try 'py help'.")
        else:
            try:
                res = cmd(msg)
                if hasattr(res,"__await__"):
                    await res
            except Exception as exc:
                logger.exception("Error processing %r", msg)
                self.print(f"Error: {exc !r}")

    def cmd_help(self, msg):
        """List commands; get details about a command"""
        args = msg.args
        if len(args) > 1:
            try:
                doc = getattr(self, f"cmd_{args[1]}").__doc__
            except AttributeError:
                self.print(f"Command {args[1]} unknown. Try 'py help'.")
            else:
                if doc is None:
                    self.print("No help text known.")
                else:
                    self.print(doc)
            return

        # Just "help": print them all
        cmds = []
        maxlen=0
        for k in dir(self):
            if not k.startswith("cmd_"):
                continue
            v = getattr(self,k)
            k = k[4:]
            if v.__doc__ is None:
                continue  # hidden
            maxlen = max(maxlen, len(k))
            cmds.append(k)

        cmds.sort()
        for k in cmds:
            v = getattr(self,f"cmd_{k}")
            s = v.__doc__.split("\n")[0]
            self.print(f"{k :{maxlen}s}: {s}")

    def print(self, s:str):
        """Print a message oon the OpenTTD console"""
        msg = openttd.internal.msg.ConsoleMsg(s)
        self.send(msg)

    def send(self, msg):
        """
        Send a message to OpenTTD
        """
        t = openttd.internal.task
        t.send(msg)

    async def main(self):
        """
        Async main loop.

        TODO.
        """
        import _ttd
        _ttd.debug(2,"Python START")

        main_storage = _ttd.object.Storage()
        main_storage.company = openttd.company.Owner.SPECTATOR
        main_storage.real_company = openttd.company.Owner.SPECTATOR
        main_storage.allow_do_command = False
        _storage.set(main_storage)
        _main.set(self)

        msg_in_w,msg_in_r = anyio.create_memory_object_stream(999)

        async with anyio.create_task_group() as tg:
            self._tg = tg
            await tg.start(self._ttd_reader, msg_in_w)
            tg.start_soon(self._process, msg_in_r)

            # TODO signal readiness to openTTD

            # just to show we're still alive
            n = 1
            while True:
                await anyio.sleep(n)
                _ttd.debug(3, f"Python running: {n}")
                n *= 2

def run():
    # protect against locale changes
    sys.stdout.reconfigure(encoding='utf-8', errors="replace")
    sys.stderr.reconfigure(encoding='utf-8', errors="replace")

    logging.basicConfig(level=logging.DEBUG)
    try:
        # TODO use asyncio when a script needs libraries that don't work with trio
        anyio.run(Main().main, backend="trio")
    except Exception as exc:
        traceback.print_exc()
        exc.__cause__ = None
        exc.__context__ = None
        raise
