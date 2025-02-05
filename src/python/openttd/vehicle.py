#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on vehicles.
"""

from __future__ import annotations

import _ttd
import openttd
from ._support.id import _ID
from .util import PlusSet, extension_of
import enum
from attrs import define,field
from ._util import with_, _WrappedList

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable

@extension_of(_ttd.script.vehicle.Type)
class Type:
    pass
VehicleType = Type

@extension_of(_ttd.script.vehicle.State)
class State:
    pass

def New(depot: Tile, engine:EngineID, cargo:CargoID|None=None) -> Vehicle:
    if cargo is None:
        vid = with_(Vehicle,_ttd.script.vehicle.build_vehicle)
    else:
        vid = with_(Vehicle,_ttd.script.vehicle.build_vehicle_with_refit,cargo)
    return vid

class Vehicle(_ID, int):
    def for_str(self) -> Iterable[str]:
        return str(self.id),self.name,

    def for_repr(self) -> Iterable[str]:
        return str(self.id),

    @staticmethod
    def is_valid(id) -> bool:
        return _ttd.script.vehicle.is_valid_vehicle(id)

    @property
    def is_primary(self) -> bool:
        return _ttd.script.vehicle.is_primary(self)

    @property
    def num_wagons(self) -> int:
        return _ttd.script.vehicle.num_wagons(self)

    @property
    def name(self) -> str|None:
        return _ttd.script.vehicle.get_name(self)

    def set_name(self, name) -> bool:
        return with_(None,_ttd.script.vehicle.set_name,self, openttd.Text(name))

    @property
    def owner(self) -> CompanyID:
        return _ttd.script.vehicle.get_owner(self)

    @property
    def tile(self) -> Tile:
        return Tile(_ttd.script.vehicle.get_location(self))

    @property
    def length(self) -> int:
        return _ttd.script.vehicle.get_length(self)

    @property
    def engine_type(self) -> int:
        return _ttd.script.vehicle.get_engine_type(self)

    @property
    def wagon_engine_type(self) -> int:
        return _ttd.script.vehicle.get_wagon_engine_type(self)

    @property
    def unit(self) -> int:
        return _ttd.script.vehicle.get_unit_number(self)

    @property
    def age(self) -> int:
        return _ttd.script.vehicle.get_age(self)

    @property
    def wagon_age(self) -> int:
        return _ttd.script.vehicle.get_wagon_age(self)

    @property
    def max_age(self) -> int:
        return _ttd.script.vehicle.get_max_age(self)

    @property
    def age_left(self) -> int:
        return _ttd.script.vehicle.get_age_left(self)

    @property
    def speed(self) -> int:
        return _ttd.script.vehicle.get_current_speed(self)

    @property
    def state(self) -> State:
        return _ttd.script.vehicle.get_state(self)

    @property
    def running_cost(self) -> Money:
        return _ttd.script.vehicle.get_running_cost(self)

    @property
    def profit_this_year(self) -> Money:
        return _ttd.script.vehicle.get_profit_this_year(self)

    @property
    def profit_last_year(self) -> Money:
        return _ttd.script.vehicle.get_profit_last_year(self)

    @property
    def value(self) -> Money:
        return _ttd.script.vehicle.get_current_value(self)

    @property
    def type(self) -> VehicleType:
        return _ttd.script.vehicle.get_vehicle_type(self)

    @property
    def road_type(self) -> RoadType:
        return _ttd.script.vehicle.get_road_type(self)

    @property
    def in_depot(self) -> bool:
        return _ttd.script.vehicle.is_in_depot(self)

    @property
    def stopped_in_depot(self) -> bool:
        return _ttd.script.vehicle.is_stopped_in_depot(self)

    def clone(depot: Tile, share_orders:bool) -> Vehicle:
        return with_(Vehicle,_ttd.script.vehicle.clone_vehicle, self.tile, self, share_orders)

    def move_wagon(self, wagon:int, dest: Vehicle,after:int) -> None:
        return with_(None,_ttd.script.vehicle.move_wagon,self, wagon, -1 if dest is None else dest, after)

    def move_wagons(self, wagon:int, dest: Vehicle,after:int) -> None:
        return with_(None,_ttd.script.vehicle.move_wagon_chain,self, wagon, -1 if dest is None else dest, after)

    def refit_capacity(self, cargo: CargoID) -> int:
        return _ttd.script.vehicle.get_refit_capacity(self, cargo)

    def refit(self, cargo: CargoID) -> None:
        return with_(None,_ttd.script.vehicle.refit,self, cargo)

    def sell(self) -> None:
        return with_(None,_ttd.script.vehicle.sell_vehicle,self)

    def sell_wagon(self, wagon:int) -> None:
        return with_(_ttd.script.vehicle.sell_wagon,self, wagon)

    def sell_wagons(self, wagon:int) -> bool:
        return with_(_ttd.script.vehicle.sell_wagon_chain,self, wagon)

    def send_to_depot(self) -> None:
        return with_(_ttd.script.vehicle.send_vehicle_to_depot,self)

    def send_to_depot_service(self) -> None:
        return with_(_ttd.script.vehicle.send_vehicle_to_depot_for_servicing,self)

    def start_stop(self) -> None:
        return with_(_ttd.script.vehicle.start_stop_vehicle,self)

    def start(self) -> bool:
        state = self.state
        if state is VS.RUNNING:
            return True
        elif state in (VS.AT_STATION,VS.STOPPED,VS.IN_DEPOT):
            with_(None,_ttd.script.vehicle.start_stop_vehicle,self)
            return True
        return False

    def stop(self) -> bool:
        state = self.state
        if state in (VS.AT_STATION,VS.STOPPED,VS.IN_DEPOT):
            return True
        elif state in (VS.RUNNING,VS.BROKEN):
            return with_(None,_ttd.script.vehicle.start_stop_vehicle,self)
        return False

    def reverse(self) -> None:
        return with_(_ttd.script.vehicle.reverse_vehicle,self)

    def capacity_for(self, cargo: CargoID) -> int:
        return _ttd.script.vehicle.get_capacity(self, cargo)

    def load_of(self, cargo: CargoID) -> int:
        return _ttd.script.vehicle.get_cargo_load(self, cargo)

    @property
    def group(self) -> GroupID:
        return _ttd.script.vehicle.get_group_id(self)

    @property
    def is_articulated(self) -> bool:
        return _ttd.script.vehicle.is_articulated(self)

    @property
    def has_shared_orders(self) -> bool:
        return _ttd.script.vehicle.has_shared_orders(self)

    @property
    def reliability(self) -> int:
        return _ttd.script.vehicle.get_reliability(self)

    @property
    def max_order_distance(self) -> int:
        return _ttd.script.vehicle.get_maximum_order_distance(self)

    @property
    def stations(self) -> StationList:
        from .stations import Stations
        return Stations(openttd.station.List_Vehicles(self))

    @property
    def order(self) -> Order:
        return openttd._.Orders(self)

class Vehicles(PlusSet[Vehicle]):
    def __init__(self, source:Iterable[Vehicle|int]=None):
        if source is None:
            source = _WrappedList(_ttd.script.vehicle.List())
        for t in source:
            self.add(_ttd.script.Vehicle(t))

    # XXX maybe add classmethods for adjacency
