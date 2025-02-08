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
from openttd.tile import Dir,TilePath
import _ttd
import enum
import os
from attrs import define,field
from .util import extension_of, PlusSet, sync, maybe_sync, classproperty
from ._util import with_, unless
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

    @classproperty
    def current(cls) -> RoadType:
        """
        Attribute to retrieve the current road type.
        """
        return _ttd.script.road.get_current_road_type()

    @staticmethod
    def set_current(road_type: RoadType):
        return unless(False, _ttd.script.road.set_current_road_type, road_type)

    @property
    def is_current(self):
        return type(self).current == self


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

@sync
def build_road(path,
               on_bridge:Callable[[TilePath],int]|None=None,
               on_error:Callable[[TilePath,TTDError],bool]|None=None,
               ) -> None:
    """
    Build a road on this path.

    @on_bridge: callback (elem -> bridge_id) that returns the bridge type to be used.

    @on_error: callback (elem, err -> bool) to handle errors. Return values:
    * `True`: retry
    * `False`: skip this leg
    * `None`: retry with one-step path elements
    For propagaging the exception, simply raise it.
    """
    BridgeType = openttd._.BridgeType
    VT_Road=openttd._.VehicleType.ROAD

    todo=None

    if on_bridge is None:
        def on_bridge(elem):
            return BridgeType.List(elem.dist).any

    if on_error is None:
        def on_error(elem, err):
            if err.err != openttd.str.error.ALREADY_BUILT:
                raise err
            return False

    todo = []
    steps = iter(path)

    while True:
        try:
            if todo:
                step = todo.pop()
                if step is None:
                    step = next(steps)
            else:
                try:
                    step = next(steps)
                except StopIteration:
                    break

            if step.d is Dir.SAME:
                continue

            if not step.jump:
                # print(f"Road from {step.start} to {step.t}")
                a = step.start
                b = step.t
                if step.next_turn and step.next_turn.jump:
                    todo.append(step)
                    todo.append(None)
                else:
                    step.build_road_to(step.start)
                continue

            # Tunnel?
            try:
                dest = step.tunnel_dest
                src = dest.tunnel_dest
            except ValueError:
                src = None
            if src is not None and src == step:
                # Yes.
                if not step.has_tunnel:
                    step.build_tunnel(VT_Road)
            else:
                # No. Build a Bridge.
                if not step.has_bridge:
                    # print(f"Bridge from {step.t} to {step.start}")
                    maybe_sync(on_bridge,step).build(VT_Road,step.t,step.start)

        except TTDError as exc:
            res = maybe_sync(on_error,step, exc)
            if res:
                # retry
                todo.append(step)
            elif res is None and step.dist > 1:
                # split to 2-tile pieces
                tile = step.start
                while tile != step.t:
                    tile += step.d
                    todo.append(TilePath(tile,step.d,dist=1))
            else:
                # continue without retrying
                continue



