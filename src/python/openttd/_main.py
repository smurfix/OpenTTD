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
from contextlib import contextmanager
from importlib import import_module
from io import StringIO
from inspect import cleandoc

from .util import maybe_async,maybe_async_threaded

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
    class CompanyID:
        pass
    class GameMode:
        pass
    class PauseState:
        pass
    class Script:
        pass

logger = logging.getLogger("OpenTTD")
log = logger.debug

_main = ContextVar("_main")
_storage = ContextVar("_storage")
estimating = ContextVar("estimating", default=True)
_async = ContextVar("_async", default=True)


@contextmanager
def test_mode():
    """
    Switch the script engine to test mode.
    Script commands will do no real work and return immediately.
    """
    try:
        token = estimating.set(True)
        yield
    finally:
        estimating.reset(token)


@define(hash=True,eq=True)
class CmdR:
    cmd:Command
    data:bytes
    company:CompanyID=field(eq=False,hash=False)
    callback: int=field(eq=False,hash=False)
    storage:Storage=field(factory=_storage.get,eq=False,hash=False)

class Obj:
    def __init__(self, **kw):
        for k,v in kw.items():
            setattr(self,k,v)

@define
class VEvent:
    """
    A rather primitive event-with-a-value type.

    There is no error/cancellation handling.
    """
    value: Any = None
    event: anyio.Event = field(factory=anyio.Event)


def _print(fn, a, kw):
    """Directly emit to the OpenTTD debug output"""
    if len(a) == 1 and not kw:
        fn(a[0])
    else:
        iof = StringIO()
        kw["file"] = iof
        print(*a, **kw)
        for s in iof.getvalue().split("\n"):
            if s == "":
                continue
            fn(s)

class Main:
    """
    The central control object.
    """
    _tg: anyio.abc.TaskGroup
    _replies:dict[CmdR, VEvent]
    _code:dict[int,BaseScript]
    _game_mode:GameMode = None
    _pause_state:PauseState = None

    def __init__(self):
        self._replies = {}
        self._globals = {}
        self._code = {}
        self._code_next = 1
        self.logger = logger
        self._pause_change = anyio.Event()

    def get_free_index(self):
        id_ = self._code_next
        self._code_next += 1
        return id_

    def get_script_indices(self) -> list[Script]:
        """
        Called from OpenTTD to get a list of vald script IDs.
        """
        return list(self._code.keys())

    def get_script_info(self, id_:int, data:Script) -> bool:
        """
        Called from OpenTTD to get information about a script.
        """
        code = self._code[id_]
        data.id = id_
        data.cls = type(code).__name__
        data.info = code.get_info()
        data.company = code.company
        return True

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
        async def hdl(msg):
            try:
                res = await maybe_async(msg.work, self)
            except Exception:
                logger.exception("Error processing %r", msg)

        async for msg in q:
            res = self._tg.start_soon(hdl,msg)

    async def handle_run(self, msg):
        # initial command line argument. Module or script file.
        try:
            try:
                # Try as a module.
                script_obj = importlib.import_module(msg.msg)
            except ImportError:
                # Try as a file.
                sf = anyio.Path(msg.msg)
                sfd = await sf.read_text()
                expr = compile(sfd,"__load__","exec")

                g = dict()
                g["openttd"] = openttd
                g["main"] = self
                eval(expr, g,g)
            else:
                await script_obj.run(self)
        except BaseException as ex:
            self.send(openttd.internal.msg.CommandRunEnd(repr(ex)))
        else:
            self.send(openttd.internal.msg.CommandRunEnd(""))


    async def handle_command(self, msg):
        args = msg.args
        try:
            cmd = getattr(self, f"cmd_{args[0]}")
        except AttributeError:
            self.print(f"Command {args[0]} unknown. Try 'py help'.")
        else:
            try:
                res = await maybe_async(cmd, args[1:])
            except Exception as exc:
                logger.exception("Error processing %r", msg)
                self.print(f"Error: {exc}")

    async def handle_result(self, msg):
        """
        Callback for our command results.
        """
        for cmdr in self._replies.keys():
            if cmdr.cmd == msg.cmd and cmdr.data == msg.data:
                break
        else:
            self.print(f"Spurious callback: {msg}")
            return

        # This part may not await
        evt = self._replies.pop(cmdr)
        st = cmdr.storage
        st.last_cmd=msg.cmd
        st.last_data=msg.data
        st.last_result = msg.result.success
        st.last_result_data=msg.resultdata
        st.last_cost = msg.result.cost
        st.last_error = 0 if msg.result.success else msg.result.error  # XXX is that correct?

        import _ttd
        _ttd.msg._done_cb(cmdr.callback, st)

        evt.value = st.result
        evt.event.set()

    async def handle_result2(self, msg):
        """
        Callback for local command results.
        """
        breakpoint()
        for k,evt in self._replies.items():
            if k.cmd == msg.cmd and k.company == msg.company:
                break
        else:
            self.print(f"Spurious callback: {msg}")
            return
        evt = self._replies.pop(k)
        breakpoint()
        evt.value = msg.result
        evt.event.set()

    def check_pending(self, cmd, data):
        """
        Check whether this command is ours.

        DANGER: this is called from the main task.
        """
        for cmdr in self._replies.keys():
            if cmdr.cmd == cmd and cmdr.data == data:
                return True
        return False

    async def cmd_start(self, args) -> VEvent:
        """Start a game script or an AI.

        Arguments:
        * ID of the company to run under. Omit if this is a game script.
          The initial company is 1.
        * the module to load. It must contain a class named "Script".
        * name=value arguments (strings)
        * name:value arguments (numbers)

        The result is the script ID.

        This command returns a VEvent structure which can be used to
        capture the script's execution state. This is mainly useful for
        automated testing.
        """
        self.print(repr(args))
        try:
            company = openttd.company.ID(int(args[0])-1)
        except ValueError:
            company = openttd.company.ID.DEITY
            if self._game_mode is None:
                raise RuntimeError("Oops: the game mode has not been set yet.")
        else:
            if openttd.company.resolve_company_id(company) < 0:
                raise ValueError(f"Company #{args[0]} does not exist.")
            if self._game_mode != openttd.internal.GameMode.NORMAL:
                raise RuntimeError("Sorry, but AIs only run when playing.")

            args = args[1:]

        return await self.do_start(*args, company=company)

    async def do_start(self, *args, company=None, **kw):
        """
        Start a script, return a VEvent to hold its result (if any).

        @company: the company to run uner, or DEITY for game scripts.

        """
        if company is None:
            company = openttd.company.ID.DEITY

        script = args[0]
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

        id_ = self.get_free_index()

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

    def _send_cmd(self, cmd, buf, cb) -> Awaitable[CommandResult]:
        # called from the command hook
        if estimating.get():
            raise RuntimeError(f"Test mode is on but command {cmd} got enqueued anyway")
        return self.send_cmd(cmd, buf, cb=cb)

    def send_cmd(self, cmd, buf, company=None, cb=0) -> Awaitable[CommandResult]:
        """
        Queue a command for execution by OpenTTD.

        This method is *not* a coroutine. It does however return an awaitable that
        resolves to the command's result.
        """
        if company is None:
            company = _storage.get().company

        cmdr = CmdR(openttd.internal.Command(cmd), buf, company, cb)
        if cmdr in self._replies:
            raise ValueError(f"Command {cmd} ({buf}) is already queued")
        evt = VEvent()
        self._replies[cmdr] = evt

        # print("TP",type(cmd),type(cmdr.data),type(company))
        self.send(openttd.internal.msg.CmdRelay(cmd, cmdr.data, company))

        if _async.get():
            return self._wait_cmd(cmdr,evt)
        return anyio.from_thread.run(self._wait_cmd,cmdr,evt)

    async def _wait_cmd(self, cmdr, evt):
        try:
            with anyio.fail_after(3):
                await evt.event.wait()
            return evt.value

        except TimeoutError:
            log(f"Command {cmdr}: no response")
            return Obj(success=False)

        except BaseException as exc:
            logger.exception(f"Command {cmdr}: error")
            raise

        finally:
            if cmdr in self._replies:
                del self._replies[cmdr]

    @property
    def game_mode(self):
        return self._game_mode

    @property
    def pause_state(self):
        return self._pause_state

    async def set_game_mode(self, mode:GameMode):
        self._game_mode = mode

        if mode != openttd.internal.GameMode.NORMAL:
            for v in list(self._code.values()):
                async with anyio.create_task_group() as tg:
                    if v.company != openttd.company.ID.DEITY:
                        v.stop();
                    else:
                        tg.start_soon(maybe_async, v.set_game_mode, mode)

    async def set_pause_state(self, mode:GameMode):
        self._pause_state = mode

        if mode != openttd.internal.GameMode.NORMAL:
            async with anyio.create_task_group() as tg:
                for v in list(self._code.values()):
                    tg.start_soon(maybe_async, v.set_pause_state, mode)

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
                self.print(f"{a}:",self._code[a].get_info())
            else:
                self.print(f"{a}: Unknown script ID.")

    def cmd_state(self, args):
        """Show script status (as suitable for restoring).

        Arguments:
        * the ID of the script to display
        """
        if len(args) != 1:
            raise ValueError("Usage: py state ID")
        self.pprint(self.code[int(args[0])].get_state())

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
        The module "openttd" is pre-loaded.

        You can use p(X) to print the value of X
        """
        from pprint import pprint

        g = self._globals
        iof = StringIO()

        g["openttd"] = openttd
        g["main"] = self

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
        def pr(s):
            self.send(openttd.internal.msg.ConsoleMsg(s))
            log(s)

        _print(pr, a, kw)

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

    def debug(self, level:int, *a, **kw):
        _print(lambda s: openttd.internal.debug(level,s), a,kw)

    async def main(self):
        """
        Async main loop.

        TODO.
        """
        import _ttd  # to access Storage; intentionally not in openttd

        openttd.internal.debug(2,"Python START")

        main_storage = _ttd.object.Storage(openttd.company.ID.SPECTATOR)
        main_storage.allow_do_command = False
        _storage.set(main_storage)
        _main.set(self)
        _ttd._main = self

        msg_in_w,msg_in_r = anyio.create_memory_object_stream(999)

        async with anyio.create_task_group() as tg:
            self._tg = tg
            estimating.set(False)

            await tg.start(self._ttd_reader, msg_in_w)
            tg.start_soon(self._process, msg_in_r)

            # TODO signal readiness to openTTD

            # just to show we're still alive
            n = 1
            while True:
                await anyio.sleep(n)
                openttd.internal.debug(3, f"Python running: {n}")
                n *= 2

def run():
    # protect against locale changes
    import _ttd
    sys.stdout.reconfigure(encoding='utf-8', errors="replace")
    sys.stderr.reconfigure(encoding='utf-8', errors="replace")

    _ttd.estimating = estimating

    v = _ttd.debug_level
    logging.basicConfig(level=logging.ERROR if v==0 else logging.WARNING if
                        v==1 else logging.INFO if v==2 else logging.DEBUG)
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
