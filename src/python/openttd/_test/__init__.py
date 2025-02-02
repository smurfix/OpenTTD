#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Test runner.
"""

from __future__ import annotations

import openttd
from importlib import import_module
from openttd.util import maybe_async_threaded
from inspect import cleandoc
from openttd.base import BaseScript
from openttd.company import Company

class TestScript(BaseScript):
    """
    Test script.

    Modes:
    0 basic work
    1 parallel idle test
    """
    ASYNC=True

    step="idle"
    async def setup(self):
        self._set_company(1)

        self.step="after setup"
        await super().setup()

    def _set_company(self, cid=None):
        self._basescript__company = openttd.company.ID.DEITY if cid is None else openttd. company.ID(cid-1)

    def get_info(self):
        return f"Test {self.__name__}, in step {self.step}"

    def set_game_mode(self, mode):
        # must implement, because we don't inherit GameScript
        pass

    async def main(self):
        self.print(f"START Test {self.__class__.__name__}")
        self.step=2
        await maybe_async_threaded(self.test)

    def test(self):
        raise NotImplementedError(f"Please fix test {self.__module__ !r}")


async def run(main, *tests):
    if not tests:
        print("Available tests ('all' runs them in-order):")
        ex = None
        for t in TESTS:
            try:
                mod = import_module(f"openttd._test.{t}")
            except Exception as exc:
                d = f"- not imported: {exc}"
                if ex is None:
                    ex = exc
            else:
                d = cleandoc(mod.__doc__ or '(no description)').split("\n")[0]
            print(f"{t :10s} {d}")

        if ex is not None:
            from traceback import print_exception
            print_exception(ex)
        return

    if tests == ("all",):
        tests = TESTS
    for t in tests:
        if t == "debug":
            breakpoint()
            continue
        mod = import_module(f"openttd._test.{t}")
        script = mod.Script
        val = await main.do_start(script, company=getattr(mod,"COMPANY",Company(1)))
        await val.event.wait()
        if isinstance(val.value,Exception):
            raise val.value

TESTS = [
    "basic",
    "delay",  # must be last, as it shuts down OpenTTD
]
