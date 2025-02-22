#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contains support for dates.
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

@extension_of(_ttd.script.date.Date)
class Date(_ID, int):
    def for_str(self)-> tuple[str, ...]:
        return int(self),self.name,

    def for_repr(self) -> tuple[str, ...]:
        return int(self),

    @staticmethod
    def is_valid(id:int) -> bool:
        return _ttd.script.date.is_valid_date(id)

    @classmethod
    def now(cls):
        return _ttd.script.date.get_current_date()

    @property
    def year(self) -> int:
        return _ttd.script.date.get_year(self)

    @property
    def month(self) -> int:
        return _ttd.script.date.get_month(self)

    @property
    def day(self) -> int:
        return _ttd.script.date.get_day_of_month(self)

    @classmethod
    def YMD(cls, year:int,month:int,day:int) -> Date:
        return _ttd.script.date.get_date(year,month,day)

    @staticmethod
    def SystemTime() -> int:
        return int(time.time())

