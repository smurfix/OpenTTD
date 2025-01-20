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
import importlib
from functools import partial
from attrs import define,field
from contextvars import ContextVar
from importlib import import_module
from io import StringIO
from inspect import cleandoc

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
    _code:dict[int,BaseScript]

    def __init__(self):
        self._replies = {}
        self._globals = {}
        self._code = {}
        self._code_next = 1
        self.logger = logger

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
                res = cmd(args[1:])
                if hasattr(res,"__await__"):
                    await res
            except Exception as exc:
                logger.exception("Error processing %r", msg)
                self.print(f"Error: {exc !r}")

    async def cmd_start(self, args):
        """Start a game script or an AI.

        Arguments:
        * ID of the company to run under. Omit if this is a game script.
        * the module to load. It must contain a class named "Script".
        * name=value arguments (strings)
        * name:value arguments (numbers)

        The result is the script ID.
        """
        self.print(repr(args))
        try:
            company = int(args[0])
        except ValueError:
            company = openttd.company.Owner.DEITY
        else:
            args = args[1:]
        script = args[0]
        kw = {}
        for val in args[1:]:
            try:
                name,v = val.split(":")
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        self.print(f"Usage error: name:number, not {val !r}")
                        return

            except ValueError:
                try:
                    name,v = val.split("=",1)
                except ValueError:
                    self.print(f"Usage error: params are name=text or name:number, not {val !r}")
                    return
            kw[name] = v

        id_ = self._code_next
        self._code_next += 1

        script_obj = importlib.import_module(script).Script(id_, company, **kw)
        try:
            res = await self._tg.start(script_obj._run)
        except StopAsyncIteration as stp:
            breakpoint()
            self.print("Stopped with",stp)
        else:
            self._code[id_] = script_obj
            return res

    def script_done(self, id_):
        """
        Callback from a script, as it ends."""
        try:
            scr = self._code.pop(id_)
        except KeyError:
            pass
        else:
            self.print(f"Script {id_} ({type(scr)}) ended.")


    def cmd_stop(self, args):
        """Stop game scripts or AIs.

        Arguments:
        * a list of script IDs to terminate
        * or "*" to stop all of them.
        """
        if len(args) == 1 and args[1] == "*":
            args = list(self._code.keys())
        elif not args:
            self.print("Usage: py stop *|ID…")
            return
        else:
            args = (int(a) for a in args)
        for a in args:
            self._code[a].stop()

    def cmd_info(self, args):
        """Show script status.

        Arguments:
        * one or more script IDs to show
        * or "*" to display a one-line summary.
        """
        if not self._code:
            self.print("No scripts are active.")
            return
        if not args or len(args) == 1 and args[0] == "*":
            args = self._code.keys()
        else:
            args = (int(a) for a in args)
        for a in args:
            if a in self._code:
                self.print(f"{a}:",self._code[a].info())
            else:
                self.print(f"{a}: Unknown script ID.")

    def cmd_state(self, args):
        """Show script status (as suitable for restoring).

        Arguments:
        * the ID of the script to display
        """
        if len(args) != 1:
            raise ValueError("Usage: py state ID")
        self.pprint(self.code[int(args[0])].state())

    def cmd_dump(self, args):
        """Show script status (as suitable for debugging).

        Arguments:
        * the ID of the script to display
        """
        if len(args) != 1:
            raise ValueError("Usage: py state ID")
        self.pprint(self.code[int(args[0])].dump())

    def cmd_reload(self, args):
        """Reload Python module(s).

        Arguments:
        * the name(s) of the module to reload.
        """
        for a in args:
            try:
                m = sys.modules[a]
            except KeyError:
                self.print(f"{a}: not loaded")
            else:
                importlib.reload(m)
                self.print(f"{a}: reloaded")


    def cmd_eval(self, args):
        """Evaluate a Python expression.
        The modules "openttd" and "_ttd" (internal) are pre-loaded.

        You can use p(X) to print the value of X
        """
        import _ttd
        from pprint import pprint

        g = self._globals
        iof = StringIO()

        g["openttd"] = openttd
        g["_ttd"] = _ttd

        g["p"] = lambda *p: print(*p, file=iof)
        g["r"] = lambda *p: print(*(repr(x) for x in p), file=iof)
        g["pp"] = partial(pprint, stream=iof)
        expr = " ".join(args)
        try:
            expr = compile(expr,"py","eval")
        except SyntaxError:
            expr = compile(expr,"py","single")
        res = eval(expr, g,g)
        if iof.getvalue():
            self.print(iof.getvalue())
        if res is not None:
            self.print(str(res))

    def cmd_help(self, args):
        """List commands; get details about a command"""
        if args:
            for arg in args:
                try:
                    doc = getattr(self, f"cmd_{arg}").__doc__
                except AttributeError:
                    self.print(f"Command {arg} unknown. Try 'py help'.")
                else:
                    if doc is None:
                        self.print(f"{arg}: No help text!")
                    else:
                        if len(args) > 1:
                            self.print(f"{arg}:")
                        for s in cleandoc(doc).split("\n"):
                            self.print(s)
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

    def print(self, *a, **kw):
        """Print something on the OpenTTD console"""
        if len(a) == 1 and not kw:
            msg = openttd.internal.msg.ConsoleMsg(a[0])
            log(a[0])
        else:
            iof = StringIO()
            kw["file"] = iof
            print(*a, **kw)
            msg = openttd.internal.msg.ConsoleMsg(iof.getvalue())
            log(iof.getvalue())
        self.send(msg)

    def pprint(self, *a, **kw):
        """Pretty-print a Python object to the OpenTTD console"""
        iof = StringIO()
        kw["stream"] = iof
        print(*a, **kw)
        self.send(openttd.internal.msg.ConsoleMsg(iof.getvalue()))
        log(iof.getvalue())

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

        main_storage = _ttd.object.Storage(openttd.company.Owner.SPECTATOR)
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
        try:
            self.send(openttd.internal.msg.ConsoleMsg(f"Python died: {exc}"))
        except Exception:
            pass
        traceback.print_exc()
        exc.__cause__ = None
        exc.__context__ = None
        raise
