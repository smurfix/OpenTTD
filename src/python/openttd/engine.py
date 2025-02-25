#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contains additional support for engines.
"""

from __future__ import annotations

import openttd
import _ttd

from .util import PlusSet, extension_of
from ._util import _WrappedList, with_
from ._support.id import _ID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self

class Engine(_ID,int):
    def for_str(self):
        return self.name,

    @staticmethod
    def is_valid(id:int):
        return _ttd.script.engine.is_valid_engine(id)

    @property
    def is_buildable(self):
        return _ttd.script.engine.is_buildable(self)

    @property
    def name(self) -> str|None:
        return _ttd.script.engine.get_name(self)

    @property
    def cargo(self) -> Cargo:
        return openttd._.Cargo(_ttd.script.engine.get_cargo_type(self))

    def can_refit_to(self, cargo:Cargo) -> bool:
        return _ttd.script.engine.can_refit_cargo(self, cargo)

    def can_pull(self, cargo:Cargo) -> bool:
        return _ttd.script.engine.can_pull_cargo(self, cargo)

    @property
    def capacity(self) -> int:
        return _ttd.script.engine.get_capacity(self)

    @property
    def reliability(self) -> int:
        return _ttd.script.engine.get_reliability(self)

    @property
    def max_speed(self) -> int:
        return _ttd.script.engine.get_max_speed(self)

    @property
    def price(self) -> Money:
        return int(_ttd.script.engine.get_price(self))

    @property
    def max_age(self) -> int:
        return _ttd.script.engine.get_max_age(self)

    @property
    def running_cost(self) -> int:
        return _ttd.script.engine.get_running_cost(self)

    @property
    def power(self) -> int:
        return _ttd.script.engine.get_power(self)

    @property
    def weight(self) -> int:
        return _ttd.script.engine.get_weight(self)

    @property
    def max_traction(self) -> int:
        return _ttd.script.engine.get_max_tractive_effort(self)

    @property
    def date_designed(self) -> int:
        return _ttd.script.engine.get_design_date(self)

    @property
    def type(self) -> VehicleType:
        return _ttd.script.engine.get_vehicle_type(self)

    @property
    def is_wagon(self) -> bool:
        return _ttd.script.engine.is_wagon(self)

    @property
    def can_run_on_rail(self, track: RailType) -> bool:
        return _ttd.script.engine.can_run_on_rail(self, track)

    @property
    def has_power_on_rail(self, track: RailType) -> bool:
        return _ttd.script.engine.has_power_on_rail(self, track)

    @property
    def rail_type(self) -> RailType:
        return _ttd.script.engine.get_rail_type(self)

    @property
    def can_run_on_road(self, track: RoadType) -> bool:
        return _ttd.script.engine.can_run_on_road(self, track)

    @property
    def has_power_on_road(self, track: RoadType) -> bool:
        return _ttd.script.engine.has_power_on_road(self, track)

    @property
    def road_type(self) -> RoadType:
        return _ttd.script.engine.get_road_type(self)

    @property
    def plane_type(self) -> PlaneType:
        return _ttd.script.engine.get_plane_type(self)

    @property
    def max_order_distance(self) -> int:
        return _ttd.script.engine.get_maximum_order_distance(self)

    @property
    def is_articulated(self) -> bool:
        return _ttd.script.engine.is_articulated(self)

    @property
    def is_articulated(self) -> bool:
        return _ttd.script.engine.is_articulated(self)

    def enable_for(self, company:Company) -> None:
        return with_(None,_ttd.script.engine.enable_for_company,self, company)

    def disable_for(self, company:Company) -> None:
        return with_(None,_ttd.script.engine.disable_for_company,self, company)


class Engines(PlusSet[Engine]):
    def __init__(self, type_: VehicleType):
        source = _WrappedList(_ttd.script.enginelist.List(type_))
        for t in source:
            self.add(Engine(t))
List=Engine.List=Engines
