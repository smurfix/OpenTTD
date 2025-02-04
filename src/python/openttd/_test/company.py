#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Basic cargo-related features.
"""

from __future__ import annotations

import anyio
import openttd
from . import TestScript

class Script(TestScript):
    def test(self):
        for c in openttd._.Company.List():
            print(c)
        c=openttd._.Company(0)
        c.set_name("HelloCo")
        assert c.name=="HelloCo", c.name
        assert str(c) == "Company:0:HelloCo", str(c)
        for c in openttd._.Company.List():
            print(c)

