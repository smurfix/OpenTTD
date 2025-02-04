#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on towns.
"""

from __future__ import annotations

import openttd
import _ttd
from .util import PlusSet
import enum
from attrs import define,field
from ._support.id import _ID
from ._util import _WrappedList, with_

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable


class Town(_ID, int):
    @staticmethod
    def is_valid(id) -> bool:
        return _ttd.script.town.is_valid_town(id)

    def for_str(self) -> Iterable[str]:
        return self.name,

    @property
    def name(self) -> str|None:
        return _ttd.script.town.get_name(self)

    def set_name(self, name) -> bool:
        return with_(None,_ttd.script.town.set_name,self, openttd.Text(name))

    def set_text(self, text: str) -> None:
        return with_(_ttd.script.town.set_text,self, openttd.Text(text))

    @property
    def population(self) -> int:
        return _ttd.script.town.get_population(self)

    @property
    def house_count(self) -> int:
        return _ttd.script.town.get_house_count(self)

    @property
    def tile(self) -> Tile:
        return Tile(_ttd.script.town.get_location(self))

    def last_month_production(self, cargo:int) -> int:
        return Tile(_ttd.script.town.get_last_month_production(self, cargo))

    def last_month_supplied(self, cargo:int) -> int:
        return Tile(_ttd.script.town.get_last_month_supplied(self, cargo))

    def last_month_transported(self, cargo:int) -> int:
        "percentage"
        return Tile(_ttd.script.town.get_last_month_transported_percentage(self, cargo))

    @property
    def last_month_received(self, effect:TownEffect) -> int:
        return Tile(_ttd.script.town.get_last_month_supplied(self, effect))

    def set_cargo_goal(self, effect:TownEffect, goal:int) -> None:
        return with_(_ttd.script.town.set_cargo_goal,self, effect, goal)

    def get_cargo_goal(self, effect:TownEffect) -> int:
        return _ttd.script.town.set_cargo_goal(self, effect)

    def set_growth_rate(self, rate:int) -> None:
        return with_(None,_ttd.script.town.set_growth_rate,self, rate)

    def get_growth_rate(self, effect:TownEffect) -> int:
        return _ttd.script.town.set_growth_rate(self)

    def d_manhattan(self, tile:Tile):
        return _ttd.script.town.get_distance_manhattan_to_tile(self, tile)

    def d_square(self, tile:Tile):
        return _ttd.script.town.get_distance_square_to_tile(self, tile)

    # IsWithinTownInfluence: Tile.is_within_town

    @property
    def has_statue(self) -> bool:
        return _ttd.script.town.has_statue(self)

    @property
    def is_city(self) -> bool:
        return _ttd.script.town.is_city(self)

    @property
    def road_rework(self) -> int:
        return _ttd.script.town.get_road_rework_duration(self)

    @property
    def funding_buildings(self) -> int:
        return _ttd.script.town.get_fund_buildings_duration(self)

    @property
    def exclusive_company(self) -> int:  # companyid
        return _ttd.script.town.get_exclusive_rights_company(self)

    @property
    def exclusive_duration(self) -> int:
        return _ttd.script.town.get_exclusive_rights_duration(self)

    def is_action_available(self, action) -> bool:
        return _ttd.script.town.is_action_available(self, action)

    def act(self, action) -> None:
        return with_(None,_ttd.script.town.perform_town_action,self,action)

    def expand(self, houses: None):
        return with_(None,_ttd.script.town.expand_town,self, houses)

    # found_town: Tile.found_town

    def rating_of(self, company:CompanyID) -> TownRating:
        return _ttd.script.town.get_rating(self, company)

    def detailed_rating_of(self, company:CompanyID) -> int:
        return _ttd.script.town.get_detailed_rating(self, company)

    def set_rating_of(self, company:CompanyID) -> None:
        return with_(None,_ttd.script.town.change_rating,self, company)

    @property
    def allowed_noise(self):
        return _ttd.script.town.get_allowed_noise(self)

    @property
    def road_layout(self) -> RoadLayout:
        return _ttd.script.town.get_road_layout(self)


class Towns(PlusSet[Town]):
    def __init__(self, source:Iterable[Town|int]=None):
        if source is None:
            source = _WrappedList(_ttd.script.townlist.List())
        for t in source:
            self.add(Town(t))

    # XXX maybe add classmethods for adjacency


Town.List = staticmethod(Towns)
