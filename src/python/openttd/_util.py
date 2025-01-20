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

def _set(p,v):
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


def _importer():
    """Reorganize the raw _ttd modules so that they look more pythonic.
    """
    import openttd as t
    import openttd._hook as th
    import _ttd

    t.internal = ti = _Sub("internal")
    ti.msg = _ttd.msg
    ti.task = _ttd.main
    ti.StopWork = StopWork
    _ttd._storage_hook = th.storage_hook

    # no-op
    ti.msg._Msg.work = lambda self,main: None
    ti.msg.ConsoleCmd.work = lambda self,main: main.handle_command(self)

    # Import submodules
    for k in (
            "accounting admin airport base bridge cargo client company "
            "date depot engine error event game goal group industry inflation infrastructure "
            "list log map marine newgrf news order rail road sign station "
            "storypage subsidy tile town tunnel vehicle viewport waypoint window"
            ).split():
        setattr(t,k,_Sub(k, getattr(_ttd.script,k,None)))
        kl=k+"list"
        vl = getattr(_ttd,kl,None)
        if vl is not None:
            setattr(getattr(t,k),"list",_Sub(f"{k}.list", getattr(_ttd,kl)))

    t.company.Owner = _ttd.support.Owner
    #t.Command=_ttd._support.Command
    #t.date.Date = _Date
    #t.date.sleep = _sleep
    #t.Text = _ttd._support.Text
    #t._control = _ttd._control

    todo = [ k for k in dir(_ttd) if k[0] != "_" and getattr(_ttd,k) not in _assigned ]
    if todo:
        import sys
        print("TODO:", *todo, file=sys.stderr)
    _assigned.clear()

