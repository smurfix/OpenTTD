#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Basic functionality test: find a town, plant a script.
"""

from __future__ import annotations

import anyio
import openttd
from openttd.base import BaseScript
from openttd._main import VEvent
from . import TestScript

class Script(TestScript):
    def test(self):
        pos = openttd._.Tile(30,30)
        ti = pos.closest_town
        tname = ti.name

        res2 = pos.Sign(f"Close to {tname}")
        res3 = (pos+(2,2)).Sign("more signage")
        assert res2 and res3 and res2 != res3, (res2,res3)
        signs = openttd._.Sign.List()
        assert len(signs) == 2
        assert len(pos.signs) == 1
        assert list(pos.signs)[0].location == pos

