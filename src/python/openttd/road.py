#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on roads.
"""

from __future__ import annotations

import openttd
import _ttd
import enum
import os
from attrs import define,field
from .util import extension_of, PlusSet
from ._util import with_
from .error import TTDError, TTDWrongTurn

import typing
from typing import overload

if typing.TYPE_CHECKING:
    Town = _ttd.script.town.Town
    from typing import Callable,Self


@extension_of(_ttd.script.road.Type)
class RoadType:
    """
    Enum for road types.
    """
    @property
    def name(self) -> str:
        return _ttd.script.road.get_name(self)

    @property
    def is_available(self) -> bool:
        return _ttd.script.road.is_road_type_available(self)

    def can_run_on(self, road_type) -> bool:
        "Can this type of vehicle run on that road?"
        return _ttd.script.road.road_veh_can_run_on_road(self, road_type)

    def has_power_on(self, road_type) -> bool:
        "Does this type of vehicle have power on that road?"
        return _ttd.script.road.road_veh_has_power_on_road(self, road_type)

    def convert(self, start:tile, end:tile) -> None:
        "convert all road tiles in this rect to my type"
        return with_(None,_ttd.script.road.convert_road_type,start,end,self)

    def cost(self, build_type:BuildType) -> Money:
        return _ttd.script.road.get_build_cost(self, build_type)

    @property
    def max_speed(self) -> int:
        return _ttd.script.road.get_max_speed(self)

    @property
    def maintainance_cost_factor(self) -> int:
        return _ttd.script.road.get_maintainance_cost_factor(self, build_type)


@extension_of(_ttd.script.road.TramTypes)
class TramType:
    """
    Enum for tram types.
    """

@extension_of(_ttd.script.road.VehicleType)
class VehicleType:
    """
    Enum for types of road vehicles
    """

@extension_of(_ttd.script.road.BuildType)
class BuildType:
    """
    Enum for types of things to build
    """

# TODO
def get_current_type() -> RoadType:
    return _ttd.script.road.get_current_road_type()
def set_current_type(road_type: RoadType):
    return with_(False,_ttd.script.road.set_current_road_type,road_type)

