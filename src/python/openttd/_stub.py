#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
Fake a _ttd module,
"""

from __future__ import annotations

import sys
from ._util import _Sub
import enum

import openttd

class Direction(enum.Enum):
    N=0
    NE=1
    E=2
    SE=3
    S=4
    SW=5
    W=6
    NW=7

class DirDiff(enum.Enum):
    S=0
    R=1
    RR=2
    B=4
    LL=6
    L=7

class Tile:
    def __init__(self,x:int|tuple[int,int], y:int|None=None):
        self.x,self.y = x if y is None else x,y
    @property
    def value(self):
        return self.x*1000000+self.y

def _importer():
    _ttd = _Sub("_ttd")
    sys.modules["_ttd"] = _ttd

    _ttd.enum=_Sub("enum")
    _ttd.enum.Direction=Direction
    _ttd.enum.DirDiff=DirDiff

    _ttd.support=_Sub("support")
    _ttd.support.Tile=Tile

    from ._support import tile
    openttd.tile = tile


