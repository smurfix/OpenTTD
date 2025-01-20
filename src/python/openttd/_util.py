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

def _importer():
    """Reorganize the raw _ttd modules so that they look more pythonic.
    """
    # First things first.
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors="replace")
    sys.stderr.reconfigure(encoding='utf-8', errors="replace")

    import openttd as t
    import _ttd

    t.internal = ti = _Sub("internal")
    ti.msg = _ttd.msg
    ti.task = _ttd.main
    ti.StopWork = StopWork

    # no-op
    ti.msg._Msg.work = lambda self,main: None
    ti.msg.ConsoleCmd.work = lambda self,main: main.handle_command(self)
