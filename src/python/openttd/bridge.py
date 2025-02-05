#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contails additional support for cargoes.
"""

from __future__ import annotations

import _ttd

from .util import PlusSet
import enum
from attrs import define,field
from openttd._util import _Sub, _WrappedList
from openttd.util import extension_of
from ._support.id import _ID
from ._util import with_, unless

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable

class BridgeType(_ID,int):

    def for_repr(self):
        return
    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.bridge.is_valid_bridge(id)

    @property
    def max_speed(self) -> int:
        return _ttd.script.bridge.get_max_speed(self)

    @property
    def price(self, length:int) -> Money:
        return _ttd.script.bridge.get_price(self, length)

    @property
    def max_length(self) -> int:
        return _ttd.script.bridge.get_max_length(self)

    @property
    def min_length(self) -> int:
        return _ttd.script.bridge.get_min_length(self)

    def build(self, roadtype: VehicleType, start:Tile, end:Tile) -> None:
        return with_(False, _ttd.script.bridge.build_bridge, roadtype, self, start, end)


class BridgeTypeList(PlusSet[BridgeType]):
    """
    A list of possible bridge types.
    """
    def __init__(self, length:int|None = None):
        for br in _WrappedList(_ttd.script.bridgelist.List()):
            br = BridgeType(br)
            if length is None or br.min_length <= length <= br.max_length:
                self.add(br)

BridgeType.List = BridgeTypeList


@define
class Bridge:
    start: Tile
    end: Tile

    def __eq__(self, other):
        if isinstance(other,Bridge):
            if self.start==other.start and self.end == other.end:
                return True
            if self.start==other.end and self.end == other.start:
                return True
            return False
        return NotImplemented

    def __contains__(self,other:Tile):
        return other == self.start or other == self.end
        # XX should we count in-between tiles as part of the bridge?

    def dest(self, other:Tile):
        if other == self.start:
            return self.end
        if other == self.end:
            return self.start
        raise ValueError(f"{other} is neither start nor end of bridge {self.start}:{self.end}")

    def type(self):
        return unless(-1, _ttd.script.bridge.get_bridge_type, self)

    def remove(self) -> None:
        return with_(None, _ttd.script.bridge.remove_bridge, self.start)


