#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
High-Level OpenTTD support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	def test_stop() -> None:
		pass

__all__ = ["run", "test_stop"]

# test_stop is defined in .base and emplaced here by .util

try:
	import _ttd
except ImportError:
	from ._stub import _importer
	_importer()
else:
	from ._util import _importer
	_importer(_ttd)
	del _ttd
del _importer

from ._main import run
