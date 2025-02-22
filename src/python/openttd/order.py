#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module lets you manage a vehicle's order list.
"""

from __future__ import annotations

import openttd
import _ttd
from .util import PlusSet, extension_of
import enum
from attrs import define,field
from ._support.id import _ID
from .vehicle import Vehicle
from ._util import with_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self
    from openttd.cargo import cargo

@extension_of(_ttd.script.order.Position)
class Position(int):
    pass

@extension_of(_ttd.script.order.Flags)
class Flags(int):
    pass

@extension_of(_ttd.script.order.Condition)
class Condition(int):
    def can_compare_as(fn: CompareFN):
        return _ttd.script.order.is_valid_conditional_order(self, fn)

@extension_of(_ttd.script.order.CompareFunction)
class CompareFN(int):
    pass

@extension_of(_ttd.script.order.StopLocation)
class StopAt(int):
    pass

@define
class Orders:
    vehicle:Vehicle

    @property
    def _(self):
        return self.vehicle

    def __getitem__(self, i) -> Order:
        return Order(self.vehicle,i)

    def __len__(self):
        return _ttd.script.order.get_order_count(self._)

    @property
    def current_in_orderlist(self) -> bool:
        return _ttd.script.order.is_current_order_part_of_orderlist(self._)

    @staticmethod
    def is_valid_condition(cond: OrderCondition, comp: CompareFunction) -> bool:
        return _ttd.script.order.is_valid_conditional_order(cond,comp)

    def append(self, destination:Tile, flags:Flags=Flags.NONE) -> None:
        with_(None, _ttd.script.order.append_order,self._, destination, flags)

    def append_conditional(self, jump_to:Position):
        with_(None, _ttd.script.order.append_conditional_order,self._, jump_to)

    def copy_from(self, source: Orders):
        with_(None, _ttd.script.order.copy_orders,self._, source._)

    def share_from(self, source: Orders):
        with_(None, _ttd.script.order.share_orders,self._, source._)

    def unshare(self):
        with_(None, _ttd.script.order.unshare_orders,self._)


@define
class Order:
    vehicle:Vehicle
    pos:int

    @property
    def _(self):
        return self.vehicle

    @property
    def is_valid(self) -> bool:
        return _ttd.script.order.is_valid_vehicle_order(self._, self.pos)

    @property
    def destination(self) -> Tile:
        return Tile(_ttd.script.order.get_order_destination(self._, self.pos))

    @property
    def flags(self) -> OrderFlags:
        return _ttd.script.order.get_order_flags(self._, self.pos)

    def set_flags(self, flags:Flags) -> None:
        return with_(None,_ttd.script.order.set_order_flags,self._, self.pos, flags)

    @property
    def jump_target(self) -> Order:
        return Order(self.vehicle, _ttd.script.order.get_order_jump_to(self._, self.pos))

    def set_jump_target(self, target:OrderPosition) -> bool:
        return with_(None,_ttd.script.order.set_order_jump_to,self._, self.pos, target)

    @property
    def condition(self) -> OrderCondition:
        return _ttd.script.order.get_order_condition(self._, self.pos)

    def set_condition(self, cond: OrderCondition) -> None:
        return with_(None, _ttd.script.order.set_order_condition,self._, self.pos, cond)

    @property
    def compare_fn(self) -> CompareFunction:
        return _ttd.script.order.get_order_compare_function(self._, self.pos)

    def set_compare_fn(self, comp: CompareFunction) -> None:
        return with_(None,_ttd.script.order.get_order_compare_function,self._, self.pos, comp)

    @property
    def compare_value(self) -> int:
        return _ttd.script.order.get_order_compare_value(self._, self.pos)

    def set_compare_value(self, value: int) -> None:
        return with_(None,_ttd.script.order.set_order_compare_value,self._, self.pos, value)

    @property
    def stop_location(self) -> StopAt:
        return _ttd.script.order.get_stop_location(self._, self.pos)

    def set_stop_location(self, loc:StopAt) -> None:
        return _ttd.script.order.set_stop_location(self._, self.pos, loc)

    @property
    def refit_cargo(self) -> Cargo:
        return Cargo(_ttd.script.order.get_order_refit(self._, self.pos))

    def set_refit_cargo(self, cargo:Cargo) -> None:
        return with_(None,_ttd.script.order.set_order_refit,self._, self.pos, cargo)

    @property
    def is_goto_station(self) -> bool:
        return _ttd.script.order.is_goto_station_order(self._, self.pos)

    @property
    def is_goto_depot(self) -> bool:
        return _ttd.script.order.is_goto_depot_order(self._, self.pos)

    @property
    def is_goto_waypoint(self) -> bool:
        return _ttd.script.order.is_goto_waypoint_order(self._, self.pos)

    @property
    def is_conditional(self) -> bool:
        return _ttd.script.order.is_conditional_order(self._, self.pos)

    @property
    def is_void(self) -> bool:
        return _ttd.script.order.is_void_order(self._, self.pos)

    @property
    def is_refit(self) -> bool:
        return _ttd.script.order.is_refit_order(self._, self.pos)

    @property
    def is_valid_conditional(self) -> bool:
        return _ttd.script.order.resolve_order_position(self._, self.pos)

    def resolve_position(self) -> OrderPos:
        return unless_(Position.INVALID, _ttd.script.order.is_refit_order, self._, self.pos)

    def insert(self, destination:Tile, flags:Flags ) -> None:
        with_(None, _ttd.script.order.insert_order,self._, self.pos, destination, flags)

    def insert_conditional(self, jump_to: Position ):
        with_(None, _ttd.script.order.insert_conditional_order,self._, self.pos, jump_to)

    def remove(self):
        with_(None, _ttd.script.order.remove_order,self._, self.pos)

    def move(self, target:Position):
        with_(None, _ttd.script.order.remove_order,self._, self.pos, target)

    def goto(self):
        """
        Execute this position next.
        """
        with_(None, _ttd.script.order.skip_to_order,self._, Position(self.pos))

