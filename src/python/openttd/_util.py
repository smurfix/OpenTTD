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

from collections.abc import Sequence

_assigned = set()

class StopWork(RuntimeError):
    pass

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
        if self._len <= i:
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
    # submodule assigner. currently unused
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
    subs = set((
            "accounting admin airport base bridge cargo client company "
            "date depot engine error event game goal group industry inflation infrastructure "
            "list log map marine newgrf news order rail road sign station "
            "storypage subsidy tile town tunnel vehicle viewport waypoint window"
            ).split())
    for k in subs:
        setattr(t,k,_Sub(k, getattr(_ttd.script,k,None)))

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

    # Now wrap all list generators (and hope that there are no collisions)
    for k in dir(_ttd.script):
        if k.endswith("list"):
            kproc(k[:-4], getattr(_ttd.script,k))
        elif (pos := k.find("list_")) > 0:
            kproc(k[:pos], getattr(_ttd.script,k))

    t.company.ID = _ttd.support.CompanyID
    ti.debug = _ttd.debug
    ti.Owner = _ttd.support.Owner
    ti.Command = _ttd.enum.Command
    ti.GameMode = _ttd.enum.GameMode
    ti.PauseState = _ttd.enum.PauseMode
    #t.Command=_ttd._support.Command
    #t.date.Date = _Date
    #t.date.sleep = _sleep
    #t.Text = _ttd._support.Text
    #t._control = _ttd._control

    t.Text = _ttd.support.Text
    t.Money = _ttd.support.Money

    t.tile.Tile = _ttd.support.Tile_

    from ._support import Tile

    t.Tile = Tile

    _copy(ti,_ttd.support,"get_")

    _assigned.clear()
    _import2()

def _import2():
    "Adjustments that are also don in stub mode"
    from .base import test_stop
    import openttd as t
    t.test_stop = test_stop

    t.tile.Transport = t.tile.TransportType
    del t.tile.TransportType

