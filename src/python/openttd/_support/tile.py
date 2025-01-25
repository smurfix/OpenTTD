#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on tiles.
"""

from __future__ import annotations

import _ttd
import openttd
import enum
from attrs import define,field

_offsets = (
    (-1, -1), # N
    (-1,  0), # NE
    (-1,  1), # E
    ( 0,  1), # SE
    ( 1,  1), # S
    ( 1,  0), # SW
    ( 1, -1), # W
    ( 0, -1), # NW
)
class Dir(enum.Enum):
    """
    Encodes a compass direction. You can add a direction to a tile to get the next
    tile in that direction. You can add a Turn to a direction to rotate it.
    """
    N=0
    NE=1
    E=2
    SE=3
    S=4
    SW=5
    W=6
    NW=7

    def xy(self):
        """
        Returns an x+y tuple to add to a tile.
        """
        return _offsets[self.value]

    def __add__(self, d):
        if isinstance(d,(Turn,_ttd.enum.DirDiff)):
            return type(self)((self.value + d.value) % 8)
        return NotImplemented

    def __radd__(self, t):
        if isinstance(t,Tile):
            off=_offsets[self.value]
            return type(t)(t.x+off[0], t.y+off[1])
        return NotImplemented

class Turn(enum.Enum):
    """
    Encodes a relative direction. (You can add them.)

    Attributes are S (same), B (back), L/R (45°) and LL/RR(90°).
    """
    S=0
    R=1
    RR=2
    BR=3
    B=4
    BL=5
    LL=6
    L=7

    def __add__(self, d):
        if isinstance(d,(Turn,_ttd.enum.DirDiff)):
            return type(self)((self.value + d.value) % 8)
        return NotImplemented


class Tile(_ttd.support.Tile):
    @property
    def xy(self):
        return (self.x,self.y)
    def __add__(self, x):
        if isinstance(x,(list,tuple)):
            return Tile(self.x+x[0], self.y+x[1])
        if isinstance(x,(Turn,_ttd.enum.DirDiff)):
            return TileDir(self.t, x)
        return NotImplemented
    def __sub__(self, t:Tile):
        return (self.x-t.x, self.y-t.y)

@define
class TileDir(Tile):
    """
    A tile with a direction.
    """
    t:Tile=field()
    d:Dir=field()
    prev:TileDir|None=field(default=None)
    dist:TileDir|None=field(default=None)
    cost:Any=None

    def __init__(self, tile, d:Dir=None, prev:TileDir=None, dist:int = 1):
        self.t = tile
        self.d = d
        self.prev = prev
        self.dist = dist

    @property
    def x(self):
        return self.t.x

    @property
    def y(self):
        return self.t.y

    def __eq__(self, other:Tile|TileDir):
        """Compare location and direction"""
        if self.t.x != other.x:
            return False
        if self.t.y != other.y:
            return False
        if self.d is None or (d := getattr(other,"d")) is None:
            return True
        return self.d == d

    def __add__(self, x, y=None):
        if x is Turn.S:
            return TileDir(self.t+self.d, self.d, prev=self.prev, dist=self.dist+1)
        if isinstance(x,(Turn,_ttd.enum.DirDiff)):
            return TileDir(Tile(self.x,self.y), self.d+x, prev=self if self.dist>0 or self.prev is None else self.prev, dist=0)

        return NotImplemented

    def __iter__(self):
        if self.prev is not None:
            yield from self.prev
        yield self


