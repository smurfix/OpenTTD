#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on signs.
"""

from __future__ import annotations

import openttd
import _ttd
from .util import PlusSet
from ._util import _WrappedList, with_
import enum
from attrs import define,field
from ._support.id import _ID

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable


class Sign(_ID, int):
    @staticmethod
    def is_valid(id) -> bool:
        return _ttd.script.sign.is_valid_sign(id)

    def for_str(self) -> Iterable[str]:
        return self.text,

    @property
    def text(self) -> str|None:
        return _ttd.script.sign.get_name(self)

    def set_text(self, text: str) -> None:
        return with_(None, _ttd.script.sign.set_name, self, openttd.Text(text))

    @property
    def location(self) -> int:
        return _ttd.script.sign.get_location(self)


class Signs(PlusSet[Sign]):
    def __init__(self, source:Iterable[Sign|int]=None):
        if source is None:
            source = _WrappedList(_ttd.script.signlist.List())
        for t in source:
            self.add(Sign(t))

    # XXX maybe add classmethods for adjacency

Sign.List = staticmethod(Signs)
