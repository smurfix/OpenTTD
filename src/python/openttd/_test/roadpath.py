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
from openttd.bridge import BridgeType
from openttd._main import VEvent
from . import TestScript
VT_Road=openttd._.VehicleType.ROAD

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

            await openttd.road.set_current_type(RoadType.ROAD)
            res = await self.subthread(pf.run)
            if res is None:
                print("ROUTING PROBLEM",a,b,ab,c,d,cd)
                return
            for k in res:
                print(k)
            print("***")
            for k in res.reversed:
                print(k)
            for k in res:
                if k.d is t.Dir.SAME:
                    continue
                if not k.jump:
                    await k.start.build_road_to(k)
                else:
                    # Tunnel?
                    try:
                        dest = k.tunnel_dest
                        src = dest.tunnel_dest
                    except ValueError:
                        pass
                    else:
                        if src == k and await tile.build_tunnel(VT_Road):
                            continue
                    # No. Bridge.
                    await BridgeType.List(k.dist).any.build(VT_Road,k.t,k.start)

        async with anyio.create_task_group() as tg:
            tg.start_soon(rtest, 50,105,"A", 70,100,"B")
#           tg.start_soon(rtest, 40,55,"C", 45,75,"D")
#           tg.start_soon(rtest, 80,31,"E", 67,32,"F")

            # XXX TODO this case doesn't work correctly:
            # * A there's an illegal turn at the NW end of the large hill.
            # * The tunnel through the small hill is not taken.
            #
            # tg.start_soon(rtest, 50,105,"", 80,31,"")
            #
            # The other way 'round works, though:
#           tg.start_soon(rtest, 80,31,"", 50,105,"")

        self.print("Paths built.")

