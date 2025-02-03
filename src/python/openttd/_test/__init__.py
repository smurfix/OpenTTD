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
import sys
from importlib import import_module
from openttd.util import maybe_async_threaded
from inspect import cleandoc
from openttd.base import BaseScript
from openttd.company import Company

class TestScript(BaseScript):
    """
    Basic test script, async mode.
    """

    step="idle"
    def setup(self):
        self._set_company(1)

        self.step="after setup"
        super().setup()

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
            print(f"{t :11s} {d}")

        print("""
            Not in "all":
debug       breaks into the debugger (Python is stopped)
bugtask     starts a debugger thread (Python continues to run)""")

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
        if t == "bugtask":
            def bug():
                breakpoint()
                pass # "c" to end the debugger, "q" to exit OpenTTD

            await main.subthread(bug)
            continue
        print(f"* Test: {t}{' (final, exiting)' if t == 'delay' else ''}", file=sys.stderr)
        mod = import_module(f"openttd._test.{t}")
        script = mod.Script
        val = await main.do_start(script, company=getattr(mod,"COMPANY",Company(1)))
        await val.event.wait()
        if isinstance(val.value,Exception):
            raise val.value
        print("  … completed.", file=sys.stderr)

TESTS = [
    "basic",
    "basic_async",
    "delay",  # must be last, as it shuts down OpenTTD
]
