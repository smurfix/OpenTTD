#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Test basic road pathfinder functionality.
"""
from __future__ import annotations

import anyio
import openttd
from openttd.base import BaseScript
from openttd.road import RoadType
from openttd._main import VEvent
from . import TestScript

class Script(TestScript):
    async def test(self):
        # TODO as soon as it's working, move the blocking stuff to a subthread
        t=openttd.tile

        # Get more money
        corp = self.company
        await corp.set_loan_amount(corp.max_loan_amount)

        async def rtest(a,b,ab,c,d,cd):
            from openttd.lib.pathfinder.road import RoadPath

            start = t.TilePath(t.Tile(a,b),t.Dir.SAME)
            dest = t.TilePath(t.Tile(c,d),t.Dir.NW)
            if ab:
                await start.Sign(ab)
            if cd:
                await dest.Sign(cd)

            pf = RoadPath((start,),(dest,))

            RoadType.set_current(RoadType.ROAD)
            assert RoadType.current == RoadType.ROAD
            res = await self.subthread(pf.run)
            if res is None:
                print("ROUTING PROBLEM",a,b,ab,c,d,cd)
                return
            for k in res:
                print(k)
            print("***")
            for k in res.reversed:
                print(k)

            await res.build_road()

        async with anyio.create_task_group() as tg:
            tg.start_soon(rtest, 50,105,"A", 70,100,"B")
            tg.start_soon(rtest, 40,55,"C", 45,75,"D")
            tg.start_soon(rtest, 80,31,"E", 67,32,"F")

            # and a more complicated one
            tg.start_soon(rtest, 50,105,"", 80,31,"")

        self.print("Paths built.")

