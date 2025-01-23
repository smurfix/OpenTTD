#
# OpenTTD example bot.
#
# This thing works as a game script or an AI.
#

import anyio
import openttd
from openttd.base import BaseScript

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
        ti = openttd.tile.get_closest_town(pos)
        self.step=5
        tname = openttd.town.get_name(ti)
        self.step=6
        self.print(f"In {tname}, {self.name} is {self.val !r}")
        self.step=7
        await anyio.sleep(3)
        self.step=8

        self.print("SEND")
        res2 = await openttd.sign.build_sign(pos, openttd.Text(f"Close to {tname}"))
        self.print("YES!" if res2.success else "no", res2)

        self.step=97
        await anyio.sleep(30)
        self.step=98
        self.print("Test task ends.")
        self.step=99


