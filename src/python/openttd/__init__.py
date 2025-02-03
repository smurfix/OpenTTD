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

import sys as _sys
from importlib import import_module as _import
from typing import TYPE_CHECKING as _CHK
import openttd as this

if _CHK:
	def test_stop() -> None:
		pass

__all__ = ["run", "test_stop"]

# test_stop is defined in .base and emplaced here by .util

try:
	import _ttd
except ImportError:
	from ._stub import _ttd
from ._util import _importer

_importer(_ttd)
del _ttd
del _importer

from ._main import run

from .base import test_stop as _ts
from . import util as _u
_u.test_stop = _ts
del _u
del _ts

# This hack is used so you can do "from openttd._ import Tile" without
# importing all up-front ... or "from openttd._ import *" if you want to do exactly that
class _imp:
	def __getattr__(self,k):
		return getattr(_import(f"openttd.{_content[k]}"),k)
	@property
	def __all__(self):
		return list(_content.keys())
	__name__ = "_"
	__package__ = f"{this.__package__}._"
	__path__ = this.__path__
	__doc__ = """
		This is a pseudo module for easy access to various OpenTTD classes.
		"""

_ = _imp()
_sys.modules["openttd._"] = _

_content = {
	'Cargo':'cargo',
	'Sign':'sign',
	'Signs':'sign',
	'Tile':'tile',
	'TilePath':'tile',
	'Dir':'tile',
	'Turn':'tile',
	'Town':'town',
	'Towns':'town',

	'TTDError':'error',
	'TTDCommandError':'error',
	'TTDResultError':'error',
}
