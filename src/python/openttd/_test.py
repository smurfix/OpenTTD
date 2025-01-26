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
    step="idle"
    async def setup(self, name="Test", val=10):
        self.name=name
        self.val=val

        self.step="after setup"
        await super().setup()

    def get_info(self):
        return f"Test script, in step {self.step}"

    async def main(self):
        self.step=1
        print(f"START Test task {openttd.internal.get_version() :08x}");
        self.print("Test task starts.")
        self.step=2

        await anyio.sleep(1)
        self.step=3
        pos = openttd.Tile(30,30)
        self.step=4
        ti = pos.closest_town
        self.step=5
        tname = openttd.town.get_name(ti)
        self.step=6
        self.print(f"In {tname}, {self.name} is {self.val !r}")
        self.step=7
        await anyio.sleep(3)
        self.step=8

        self.print("SEND")
        res2 = await openttd.sign.build_sign(pos._, openttd.Text(f"Close to {tname}"))
        self.print("YES!" if res2.success else "no", res2)

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


async def run(main):
    """Called when openttd is started with '-Y openttd._test'"""
    res = await main.cmd_start("openttd._test")
    await res.wait()
    if


