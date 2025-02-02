#
# OpenTTD example bot.
#
# This thing works as a game script or an AI.
#

import anyio
import openttd
from openttd.base import BaseScript
from openttd._main import VEvent

class Script(BaseScript):
    """
    Test script.

    Modes:
    0 basic work
    1 parallel idle test
    """

    step="idle"
    async def setup(self, name="Test", val=10, mode=0):
        self.name=name
        self.val=val
        if mode == 0:
            import os
            m = os.environ.get("PYTTD_MODE",0)
            if m:
                mode = int(m)
        self.mode=mode

        self.step="after setup"
        await super().setup()

    def get_info(self):
        return f"Test script, mode {self.mode}, in step {self.step}"

    async def test_basic(self):
        self.step=3
        pos = openttd.Tile(30,30)
        self.step=4
        ti = pos.closest_town
        self.step=5
        tname = openttd.town.get_name(ti)
        self.step=6
        self.print(f"In {tname}, {self.name} is {self.val !r}")
        self.step=7
        # await anyio.sleep(3)
        self.step=8

        self.print("SEND")
        res2 = await openttd.sign.build_sign(pos._, openttd.Text(f"Close to {tname}"))
        self.print("YES!" if res2.success else "no", res2)

    async def test_delay(self):
        self.step=90
        def ts(n):
            import time
            self.step=95
            for _ in range(n):
                time.sleep(1)
                openttd.test_stop()
            self.step=96
            return 42
        async def pling():
            self.print("Pling")
            await anyio.sleep(5)
            self.print("Plang")
            await anyio.sleep(5)
            self.print("Plong")
        async with anyio.create_task_group() as tg:
            tg.start_soon(pling)
            res = await self.subthread(ts,30)
        if res != 42 or self.step != 96:
            raise RuntimeError("ERROR")
        self.step=98
        self.print("Test task ends.")
        self.step=99

    async def test_roadpath(self):
        # TODO as soon as it's working, move the blocking stuff to a subthread
        t=openttd.tile
        async def rtest(a,b,ab,c,d,cd):
            from openttd.lib.pathfinder.road import Road
            start = t.TileDir(t.Tile(a,b),t.Dir.SAME)
            dest = t.TileDir(t.Tile(c,d),t.Dir.NW)
            if ab:
                await openttd.sign.build_sign(start._, openttd.Text(ab))
            if cd:
                await openttd.sign.build_sign(dest._, openttd.Text(cd))

            pf = Road((start,),(dest,))

            openttd.road.set_current_road_type(openttd.road.Type.ROAD)
            res = await self.subthread(pf.run)
            for k in res:
                print(k)
            print("***")
            for k in res.reversed:
                print(k)
            if res is None:
                print(f"No road {start} {desc}")
                await anyio.sleep(10)
            for k in res:
                if k.d is t.Dir.SAME:
                    continue
                if not k.jump:  # bridges and tunnels are TODO
                    await k.prev_turn.build_road_to(k)

        async with anyio.create_task_group() as tg:
            tg.start_soon(rtest, 50,105,"A", 70,100,"B")
            tg.start_soon(rtest, 40,55,"C", 45,75,"D")
            tg.start_soon(rtest, 80,31,"E", 67,32,"F")

            # XXX TODO this case doesn't work correctly:
            # * A there's an illegal turn at the NW end of the large hill.
            # * The tunnel through the small hill is not taken.
            #
            # tg.start_soon(rtest, 50,105,"", 80,31,"")
            #
            # The other way 'round works, though:
            # tg.start_soon(rtest, 80,31,"", 50,105,"")

        await anyio.sleep(30)

    async def main(self):
        self.print(f"START Test, mode={self.mode}")
        self.step=2

        tests = [
            self.test_basic,  # 1
            self.test_delay,  # 2
            self.test_roadpath,  # 3
        ]

        if self.mode == 0:
            for t in tests:
                await t()
        else:
            await tests[self.mode-1]()


async def run(main):
    """Called when openttd is started with '-Y openttd._test'"""
    res = await main.do_start("openttd._test")
    await res.event.wait()
    if isinstance(res.value,Exception):
        raise res.value
    elif isinstance(res.value,BaseException):
        print(repr(res.value), file=sys.stderr)
        raise SystemExit(2)
    else:
        return "OK"


