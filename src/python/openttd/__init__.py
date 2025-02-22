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

# This hack is used so you can call "openttd._.Tile" ad-hoc.
# Alternately, "from openttd._ import *" works too.
class _imp:
    def __getattr__(self,k):
        if k[0] == "_":
            raise AttributeError(k)
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
    'Bridge':'bridge',
    'BridgeType':'bridge',
    'BuildType':'tile',
    'Cargo':'cargo',
    'CargoClass':'cargo',
    'Company':'company',
    'Date':'date',
    'Depots':'tile',
    'Dir':'tile',
    'Engine':'engine',
    'Engines':'engine',
    'Path':'tile',
    'RoadBuildType':'road',
    'RoadVehicleType':'road',
    'RoadType':'road',
    'Sign':'sign',
    'Signs':'sign',
    'SpecialStationID':'station',
    'Station':'station',
    'Stations':'station',
    'TerrainType':'tile',
    'Tile':'tile',
    'TilePath':'tile',
    'Tiles':'tile',
    'Town':'town',
    'Towns':'town',
    'TransportType':'tile',
    'Turn':'tile',
    'Vehicle':'vehicle',
    'Vehicles':'vehicle',
    'VehicleType':'vehicle',

    'TTDError':'error',
    'TTDCommandError':'error',
    'TTDResultError':'error',
}
