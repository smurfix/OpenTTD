#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This submodule is used to re-organize the raw _ttd import.
"""

from __future__ import annotations

import _ttd
from collections.abc import Sequence
from .error import TTDCommandError

from attrs import define,field,validators

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable

_assigned = set()


class StringTab:
    """
    String mapping.
    """
    _sub:dict[str,StringTab]=None
    _ids:dict[str,int]=None

    def __init__(self):
        self._sub=dict()
        self._ids=dict()

    def bool(self):
        return bool(self._sub) or bool(self._ids)
    def __setattr__(self,k,v):
        if k[0] == "_":
            object.__setattr__(self,k,v)
        else:
            self._sub[k] = v
    def __setitem__(self,k,v):
        self._ids[k] = v
    def __getattr__(self,k):
        if k in self._sub:
            return self._sub[k]
        return self._ids[k]
    def __dir__(self):
        res = []
        if self._sub is not None:
            res.extend(self._sub.keys())
        if self._ids is not None:
            res.extend(self._ids.keys())
        if not res:
            res = super().__dir__()
        return res


def with_(Wrap:type, proc, *a, **kw):
    """
    Generate a result type or an error, whether or not we're in async context.

    Usage::

        sign = [await] with_(Sign,ttd.script.sign.make_sign(Text("Hello")))

    The 'await' is necessary *only* in async mode.
    """
    from openttd._main import _async

    def _resolve(result, maybe_async=True):
        if maybe_async:
            if hasattr(result,"__await__"):
                # Definitely in async mode. Retrieve the result and retry.
                async def hdl():
                    return _resolve(await result, maybe_async=False)
                return hdl()
            if _async.get():
                # Async mode, but the call returned without issuing a command.
                # Wrap us.
                async def hdl():
                    return _resolve(result, maybe_async=False)
                return hdl()

        if Wrap is None:
            if not result:
                raise TTDCommandError(proc,a,kw)
            return result
        if Wrap is False:
            return result
        if isinstance(result,list):
            return Wrap(*result)
        else:
            # presumably this didn't work
            raise TTDCommandError(proc,a,kw,result)

    return _resolve(proc(*a,**kw))

def unless(err, proc, *a, **kw):
    """
    Call this non-command method and return its result.
    "err" indicates an error that is not otherwise signalled.
    """
    result = proc(*a,**kw)
    if hasattr(result,"__await__"):
        raise RuntimeError(f"Owch. {proc} is supposed not to be async")
    if result == err:
        raise TTDError(proc,a,kw)
    return result


class StopWork(RuntimeError):
    pass

class Unknown:
    def __init__(self, path,repr_):
        self.p = path
        if repr_.startswith('<') and repr_.endswith('>'):
            repr_ = repr_[1:-1]
        self.r = repr_
    def __repr__(self):
        return f"‹{self.p:self.r}›"

class _Sub:
    """A simple pseudo-submodule"""
    def __init__(self, name, m=None):
        self.__name = name
        if m is not None:
            _assigned.add(m)
            for k in dir(m):
                if k.startswith("_"):
                    continue
                v = getattr(m,k)
                if v in _assigned:
                    continue
                _assigned.add(v)
                setattr(self,k,v)

    def __repr__(self):
        return f'‹{self.__name}›'
    def __str__(self):
        return self.__name

class _WrappedList(Sequence):
    def __init__(self, data):
        self._data = data
        self._cache = []
        self._len = self._data.count()

    def _fill(self, i:int=None):
        while len(self._cache) < self._len and (i is None or i >= len(self._cache)):
            if self._cache:
                nx = self._data.next()
            else:
                nx = self._data.begin()
            self._cache.append(nx)

    def __getitem__(self, i):
        if i < 0:
            i = self._len + i
        if len(self._cache) <= i:
            self._fill(i)
        return self._cache[i]

    def __len__(self):
        return self._len

    def __iter__(self):
        self._fill()
        return iter(self._cache)

    def get_value(self, k):
        "Retrieve the value associated with an item, *not* an index!"
        return self._data.get_value(k)

class _ListWrap:
    def __init__(self, cls):
        self.cls = cls
    def __call__(self, *a, **kw):
        return _WrappedList(self.cls(*a, **kw))

def _set(p,v):
    # submodule assigner.
    m = t
    p = p.split(".")
    vp = []
    for k in p[:-1]:
        vp.append(k)
        try:
            m = getattr(m,k)
        except AttributeError:
            mn = _Sub('.'.join(vp))
            setattr(m,k,mn)
            m = mn

    _assigned.add(v)
    setattr(m,p[-1],v)


# the following is a simplified version of "outcome".
# We do this because Trio will unpack us.

def capture(sync_fn, *args, **kwargs):
    try:
        return Value(sync_fn(*args, **kwargs))
    except Exception as exc:
        return Error(exc)

class Outcome:
    pass

@define(frozen=True, repr=False, slots=True)
class Value(Outcome):
    value = field()

    def __repr__(self):
        return f'Value({self.value!r})'

    def unwrap(self):
        return self.value


@define(frozen=True, repr=False, slots=True)
class Error(Outcome):
    error = field(validator=validators.instance_of(Exception))

    def __repr__(self):
        return f'Error({self.error!r})'

    def unwrap(self):
        captured_error = self.error
        try:
            raise captured_error
        finally:
            del captured_error, self

## end of Outcome


def _copy(dst,src,prefix=""):
    # attribute copier
    for k in dir(src):
        if prefix:
            if not k.startswith(prefix):
                continue
        else:
            if k[0] == "_":
                continue
        if hasattr(dst,k):
            continue
        setattr(dst,k,getattr(src,k))


def _cmd_data_repr(self):
    "__repr__ for CommandData"
    return f"‹CmdData:{self.cmd.name}›"

def _cmd_res_repr(self):
    "__repr__ for CmdResult"
    return f"‹CmdRes:{self.cmd.name}:{self.resultdata !r}›"


def _importer(_ttd):
    """
    Reorganize the raw _ttd modules so that they look more pythonic.
    """
    # First things first.
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors="replace")
    sys.stderr.reconfigure(encoding='utf-8', errors="replace")

    import openttd as t
    import openttd._hook as th

    t.str = _ttd._add_strings(StringTab)
    t.internal = ti = _Sub("internal")

    ti.msg = _ttd.msg
    ti.task = _ttd._task
    ti.StopWork = StopWork

    _ttd._command_hook = th.command_hook
    _ttd._storage_hook = th.storage_hook
    _ttd.list = _Sub("_ttd.list")

    # Install message handlers from _msg in msg objects
    import openttd._msg as msg
    for k in dir(_ttd.msg):
        if k[0] == "_":
            continue
        if hasattr(msg,k):
            getattr(_ttd.msg, k).work = getattr(msg, k)

    # the default is to do complain (heh)
    ti.msg._Msg.work = lambda self,main: main.print(f"Message not handled: {self}")

    # Import submodules
    def kproc(name, src):
        tt = getattr(_ttd.script, name, None)
        tx = getattr(t, name, None)
        if tt is None:
            tt = _Sub(f"_ttd.script.{name}")
            setattr(_ttd.list,name,tt)
        if tx is None:
            tx = _Sub(f"openttd.{name}")
            setattr(t,name,tt)
        for k in dir(src):
            if k[0] == "_":
                continue
            v = getattr(src,k)
            k_orig = k
            if k.lower().startswith(name):
                k = k[len(name):]
            if k.lower().startswith("list"):
                v = _ListWrap(v)
            if hasattr(tx,k):
                print("SKIP",name,k_orig)
            else:
                setattr(tx,k,v)

    # Now wrap list generators (and hope that there are no collisions)
    for k in dir(_ttd.script):
        if k.endswith("list"):
            kproc(k[:-4], getattr(_ttd.script,k))
        elif (pos := k.find("list_")) > 0:
            kproc(k[:pos], getattr(_ttd.script,k))

#    t.company.ID = _ttd.support.CompanyID
    ti.debug = _ttd.debug
    ti.Owner = _ttd.support.Owner
    ti.Command = _ttd.enum.Command
    ti.GameMode = _ttd.enum.GameMode
    ti.PauseState = _ttd.enum.PauseMode
    _ttd.support.CommandData.__repr__ = _cmd_data_repr
    _ttd.msg.CmdResult.__repr__ = _cmd_res_repr
    #t.Command=_ttd._support.Command
    #t.date.Date = _Date
    #t.date.sleep = _sleep
    #t.Text = _ttd._support.Text
    #t._control = _ttd._control

    t.Text = _ttd.support.Text
    t.Money = _ttd.support.Money


#   from . import _support as _s
#   t.Tile = _s.Tile
#   t.tile.Turn = _s.Turn
#   t.tile.Dir = _s.Dir
#   t.tile.TilePath = _s.TilePath

#   from ._support import town as _sto
#   t.Town = _sto.Town

#   from ._support import towns as _stos
#   t.Towns = _stos.Towns

#   from ._support import station as _st
#   t.station.SpecialIDs = _st.ID

#   _copy(ti,_ttd.support,"get_")

#   _assigned.clear()
    _import2()

def _import2():
    "Adjustments that are also don in stub mode"
    from .base import test_stop
    from ._main import test_mode, estimating
    import openttd as t
    import openttd.tile
    t.test_stop = test_stop
    t.test_mode = test_mode
    t.estimating = estimating

#    t.tile.Transport = t.tile.TransportType
#    del t.tile.TransportType

