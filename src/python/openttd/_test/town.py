#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Test basic town features.
"""
from __future__ import annotations

import anyio
import openttd
from openttd.base import BaseScript
from openttd._main import VEvent
from . import TestScript

class Script(TestScript):
    def test(self):
        for t in openttd._.Town.List():
            print(f"{t} ({t.population})")
        print(f"Largest: {openttd._.Town.List().max(lambda x:x.population)}")
        print("Smallest two:")
        for t in openttd._.Town.List().min_n(2,lambda x:x.population):
            print(f"{t} ({t.population})")

