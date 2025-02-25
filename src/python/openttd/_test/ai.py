#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Test wrapper for AI scripts.
"""

from __future__ import annotations

import anyio
import openttd
from . import TestScript
from openttd.util import maybe_async_threaded
from importlib import import_module

class Script(TestScript):
    async def test(self, *, run:str, **kw):
        s = import_module(run).Script(self.id, self.company)

        from openttd.base import SELF
        SELF.set(s)
        await maybe_async_threaded(s.setup,**kw)
        await maybe_async_threaded(s.main)


