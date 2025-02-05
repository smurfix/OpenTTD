#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the+ GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without+ even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the+ GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contains generic support for things that have an ID.
"""

from __future__ import annotations

class _ID:
    """
    A simple wrapper that encapsulates, well, something.

    As you override this, set '_Compat' to a list of classes which are OK
    to compare against this one, and '_Base' to the type used for
    typecasting (to prevent recursion, and all that). The default for the
    latter is "int" for convenience.

    This way we (try to) prevent comparing incommensurable objects. A
    station is not a vehicle even if they happen to have the same ID.

    This class intentionally does not use a container for whatever it
    subclasses because nanobind can't auto-cast them back,

    The long term fix is to use strong types in the underlying OpenTTD
    code, but that's a different (and quite code-churn-y) problem.
    """
    _Compat:ClassVar[Tuple[type,...]] = ()
    _Base:ClassVar[type] = int

    def __new__(cls, *a,**kw):
        if not cls.is_valid(*a,**kw):
            raise ValueError(f"Invalid ID {id} for {type(self)}")
        return super().__new__(cls,*a,**kw)

    @staticmethod
    def is_valid(id_) -> bool:
        return True

    def for_str(self) -> list[str]:
        """
        Additional info for `__str__`.

        Override and append your data.
        """
        return [int(self)]

    def __bool__(self):
        return True

    def __hash__(self):
        return self._Base(self)

    def __eq__(self, other):
        if type(other) is not type(self) and type(other) not in self._Compat:
            return NotImplemented
        return self._Base(self) == self._Base(other)

    def __ne__(self, other):
        if type(other) is not type(self) and type(other) not in self._Compat:
            return NotImplemented
        return self._Base(self) != self._Base(other)

    def for_repr(self) -> tuple[str,...]:
        """Additional info for `__repr__`.

        Override and append your data.
        """
        return int(self),

    def __str__(self) -> str:
        fr=":".join(str(x) for x in self.for_str())
        return f"{type(self).__name__}:{fr}"

    def __repr__(self) -> str:
        fr=",".join(repr(x) for x in self.for_repr())
        return f"{type(self).__name__}({fr})"
