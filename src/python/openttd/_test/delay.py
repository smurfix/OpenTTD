#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Test that concurrent jobs get terminated correctly when the game terminates.
"""

from __future__ import annotations

import anyio
import openttd
from openttd.base import BaseScript
from openttd._main import VEvent,_main
import time
from . import TestScript

class Script(TestScript):

    async def test(self):
        self.step=90
        def ts(n):
            self.step=95
            for _ in range(n*10):
                time.sleep(0.1)
                openttd.test_stop()
            self.step=96
            return 42
        async def pling():
            self.print("Pling")
            await anyio.sleep(5)
            self.print("Plang")
            await anyio.sleep(5)
            self.print("Plong")

        t1 = time.monotonic()
        try:
            async with anyio.create_task_group() as tg:
                tg.start_soon(pling)
                tg.start_soon(self.subthread,ts,10)
                await anyio.sleep(1.5)
                self.print("Test task terminates.")
                _main.get().send(openttd.internal.msg.CommandRunEnd(""))

        finally:
            t2 = time.monotonic()
            assert 1 < t2-t1 < 3, f"Test took {t2-t1 :.1f} seconds!"


