#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
This 'test' runs a debug session in a thread.
"""

from __future__ import annotations

import anyio
import openttd
from openttd.base import BaseScript
from openttd._main import VEvent
from . import TestScript
from .._ import TTDError

class Script(TestScript):

    def test(self):
        breakpoint()
        pass # "c" to end the debugger, "q" to exit OpenTTD
