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

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable

@extension_of(_ttd.script.cargo.TownEffect)
class TownEffect(_ID,int):

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.cargo.is_valid_town_effect(id)

#@extension_of(_ttd.script.cargo.Cargo)
class Cargo(_ID, int):
    def for_str(self)-> tuple[str, ...]:
        return int(self),self.name,

    def for_repr(self) -> tuple[str, ...]:
        return int(self),

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.cargo.is_valid_cargo(id)

    @property
    def name(self) -> str|None:
        return _ttd.script.cargo.get_name(self)

    @property
    def label(self) -> str|None:
        return _ttd.script.cargo.get_cargo_label(self)

    @property
    def is_freight(self) -> bool:
        return _ttd.script.cargo.is_freight(self)

    def has_class(self, cls:CargoClass) -> bool:
        return _ttd.script.cargo.has_class(self, cls)

    def town_effect(self) -> TownEffect:
        return _ttd.script.cargo.get_town_effect(self)

    def income_for(self, distance:int, days:int) -> Money:
        return _ttd.script.cargo.get_cargo_income(self, distance, days)

    @property
    def distribution_type(self) -> DistributionType:
        return _ttd.script.cargo.get_distribution_type(self)

    def weight_for(self, amount:int) -> int:
        return _ttd.script.cargo.get_weight(self, amount)

    @property
    def road_vehicle_type(self):
        return _ttd.script.road.get_road_vehicle_type_for_cargo(self)

##### Lists #####


class Cargoes(PlusSet[Cargo]):
    """
    A list of possible cargoes.

    The default is all cargoes unless you limit it.
    """
    def __init__(self, source:Iterable[Cargo|int]=None):
        if source is None:
            source = _WrappedList(_ttd.script.cargolist.List())
        for c in source:
            self.add(Cargo(c))

    @classmethod
    def AcceptedByIndustry(cls, industry:Industry):
        return cls(_ttd.script.cargolist.IndustryAccepting(industry._))

    @classmethod
    def ProducedByIndustry(cls, industry:Industry):
        return cls(_ttd.script.cargolist.IndustryProducing(industry._))

    @classmethod
    def AcceptedByStation(cls, station:Station):
        return cls(_ttd.script.cargolist.StationAccepting(station._))

Cargo.List=Cargoes
Cargo.AcceptedByIndustry=Cargoes.AcceptedByIndustry
Cargo.ProducedByIndustry=Cargoes.ProducedByIndustry
Cargo.AcceptedByStation=Cargoes.AcceptedByStation
