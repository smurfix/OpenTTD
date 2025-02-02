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

from .plus import PlusSet
import enum
from attrs import define,field
from openttd._util import _Sub
from openttd.util import extension_of
from .id import _ID

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable

_IDS = _ttd.script.cargo.SpecialCargoIDs
for k in dir(_IDS):
    if not k.startswith("CT_"):
        continue
    setattr(ID, k[3:], getattr(_ID,k))

@extension_of(_ttd.script.cargo.TownEffect)
class TownEffect(_ID,int):

    @staticmethod
    def is_valid(id:int):
        return _ttd.script.cargo.is_valid_town_effect(id)

@extension_of(_ttd.script.cargo.Cargo)
class Cargo(_ID, int):
    def for_str(self):
        return self.name,

    @staticmethod
    def is_valid(id:int):
        return _ttd.script.cargo.is_valid_cargo(id)

    @property
    def name(self) -> str|None:
        return _ttd.script.cargo.get_name(self._)

    @property
    def label(self) -> str|None:
        return _ttd.script.cargo.get_cargo_label(self._)

    @property
    def is_freight(self) -> bool:
        return _ttd.script.cargo.is_freight(self._)

    def has_class(self, cls:CargoClass) -> bool:
        return _ttd.script.cargo.has_class(self._, cls)

    def town_effect(self) -> TownEffect:
        return _ttd.script.cargo.get_town_effect(self._)

    def income_for(self, distance:int, days:int) -> Money:
        return _ttd.script.cargo.get_cargo_income(self._, distance, days)

    @property
    def distribution_type(self) -> DistributionType:
        return _ttd.script.cargo.get_distribution_type(self._)

    def weight_for(self, amount:int) -> int:
        return _ttd.script.cargo.get_weight(self._, amount)

##### Lists #####


from .plus import PlusSet

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Iterable

class Cargoes(PlusSet[Cargo]):
    """
    A list of possible cargoes.

    The default is all cargoes unless you limit it.
    """
    def __init__(self, source:Iterable[Cargo|int]=None):
        if source is None:
            source = _ttd.script.cargolist.List()
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

