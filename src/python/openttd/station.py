#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contains additional support for stations.
"""

from __future__ import annotations

import _ttd

from .util import PlusSet
import enum
from attrs import define,field
import openttd
from openttd._util import _Sub, _WrappedList
from openttd.util import extension_of
from ._support.id import _ID

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable
    from .cargo import Cargo

@extension_of(_ttd.script.basestation.SpecialStationIDs)
class SpecialStationID(_ID,int):
    pass
SpecialID = SpecialStationID
SpecialID.NEW = SpecialID.STATION_NEW
SpecialID.INVALID = SpecialID.STATION_INVALID
SpecialID.JOIN_ADJACENT = SpecialID.STATION_JOIN_ADJACENT

@extension_of(_ttd.script.station.Type)
class StationType(_ID,int):

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.station.is_valid_town_effect(id)

    @property
    def coverage(self) -> int:
        return _ttd.script.station.get_coverage_radius(self)

Type = StationType

#@extension_of(_ttd.script.station.station)
class BaseStation(_ID, int):

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.basestation.is_valid_basestation(id)

    @property
    def name(self) -> str|None:
        return _ttd.script.basestation.get_name(self)

    def set_name(self, name) -> None:
        return with_(None,_ttd.script.basestation.set_name,self, openttd.Text(name))

    @property
    def location(self) -> Tile:
        return _ttd.script.basestation.get_location(self)

    @property
    def construction_date(self) -> Date:
        return _ttd.script.basestation.get_construction_date(self)

class Station(BaseStation):
    def for_str(self)-> tuple[str, ...]:
        return int(self),self.name,

    def for_repr(self) -> tuple[str, ...]:
        return int(self),

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.station.is_valid_station(id)

    @property
    def owner(self) -> Company|None:
        return openttd._.Company(_ttd.script.station.get_owner(self))

    def cargo_waiting(self, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_waiting(self, cargo)

    def cargo_waiting_from(self, from_: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_waiting_from(self, from_, cargo)

    def cargo_waiting_via(self, via: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_waiting_via(self, via, cargo)

    def cargo_waiting_from_via(self, from_: Station, via: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_waiting_from_via(self, from_, via, cargo)


    def cargo_planned(self, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_planned(self, cargo)

    def cargo_planned_from(self, from_: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_planned_from(self, from_, cargo)

    def cargo_planned_via(self, via: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_planned_via(self, via, cargo)

    def cargo_planned_from_via(self, from_: Station, via: Station, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_planned_from_via(self, from_, via, cargo)


    def has_rating_for(self, cargo: Cargo) -> bool:
        return _ttd.script.station.has_cargo_rating(self, cargo)

    def rating_for(self, cargo: Cargo) -> int:
        return _ttd.script.station.get_cargo_rating(self, cargo)

    @property
    def coverage(self, cargo: Cargo) -> bool:
        return _ttd.script.station.get_station_coverage_radius(self)

    def d_manhattan(self, tile:Tile) -> int:
        return _ttd.script.station.get_distance_manhattan_to_tile(self, tile)

    def d_square(self, tile:Tile) -> int:
        return _ttd.script.station.get_distance_square_to_tile(self, tile)

    def is_within_town(self, town:Town) -> bool:
        return _ttd.script.station.is_within_town_influence(self, town)

    def has_type(self, type: StationType) -> bool:
        return _ttd.script.station.has_station_type(self, type)

    def has_road_type(self, type: RoadType) -> bool:
        return _ttd.script.station.has_road_type(self, type)

    def tiles_for(self, type_:StationType) -> PlusSet[Tile]:
        res = PlusSet()
        checked = set()
        todo = self.location.Rect(2)
        while todo:
            t = todo.pop()
            checked.add(t)
            if not t.has_station:
                continue
            if t.station != self:
                continue
            if type_==StationType.ROAD:
                f = t.is_road_station or t.is_drivethru_road_station
            else:
                raise NotImplementedError("TypeCheck")
            if f:
                res.add(self)
            todo.add(t.Rect(2)-checked)
        return res


    @property
    def closest_town(self):
        return openttd._.Town(_ttd.script.station.get_nearest_town(self))

    @property
    def is_closed(self) -> bool:
        # only for airports
        return openttd.station.is_airport_closed(self)

    def open_close(self) -> bool:
        return with_(False, openttd.station.open_close_airport,self)

    def open(self) -> bool:
        if not self.closed:
            return True
        return with_(False,openttd.station.open_close_airport,self)

    def close(self) -> bool:
        if self.closed:
            return True
        return with_(False,openttd.station.open_close_airport,self)


    @property
    def vehicles(self):
        return openttd._.Vehicles(_WrappedList(_ttd.script.vehiclelist.Station(self)))

Station.NEW = SpecialID.STATION_NEW.value
Station.INVALID = SpecialID.STATION_INVALID.value
Station.JOIN_ADJACENT = SpecialID.STATION_JOIN_ADJACENT.value


@extension_of(_ttd.script.stationlist.Selector)
class Selector(_ID,int):
    pass

@extension_of(_ttd.script.stationlist.Mode)
class Mode(_ID,int):
    pass


class Stations(PlusSet[Station]):
    def __init__(self, type_:StationType|None=None, source=None):
        if source is None:
            source = _WrappedList(_ttd.script.stationlist.List(type_))
        for s in source:
            self.add(Station(s))

# TODO all those cargo by-from/via/destination lists
