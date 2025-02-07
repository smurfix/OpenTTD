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
from openttd.error import TTDCommandError
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
            todo=None

            async def rd(a,b):
                try:
                    await a.build_road_to(b)
                except TTDCommandError as err:
                    if err.err != openttd.str.error.ALREADY_BUILT:
                        print("ERR ROAD {a} {b} {err}")
                        await a.Sign(f"ERR {a}")
                        await b.Sign(f"ERR {b}")
                        #raise

            for k in res:
                if k.d is t.Dir.SAME:
                    continue
                if not k.jump:
                    print(f"Road from {k.start} to {k.t}")
                    a = k.start
                    b = k.t
                    if k.next_turn and k.next_turn.jump:
                        todo = (a,b)
                    else:
                        await rd(a,b)
                    continue

                # Tunnel?
                try:
                    dest = k.tunnel_dest
                    src = dest.tunnel_dest
                except ValueError:
                    src = None
                if src is not None and src == k:
                    if not k.has_tunnel:
                        try:
                            await k.build_tunnel(VT_Road)
                        except Exception as exc:
                            print("OWCH",exc)
                            await k.Sign(f"ERR {k}")
                            await k.start.Sign(f"ERR {k.start}")
                else:
                    # No. Build a Bridge.
                    if not k.has_bridge:
                        print(f"Bridge from {k.t} to {k.start}")
                        await BridgeType.List(k.dist).any.build(VT_Road,k.t,k.start)

                if todo:
                    await rd(*todo)
                    todo=None

        async with anyio.create_task_group() as tg:
            tg.start_soon(rtest, 50,105,"A", 70,100,"B")
            tg.start_soon(rtest, 40,55,"C", 45,75,"D")
            tg.start_soon(rtest, 80,31,"E", 67,32,"F")

            # and a more complicated one
            tg.start_soon(rtest, 50,105,"", 80,31,"")

        self.print("Paths built.")

