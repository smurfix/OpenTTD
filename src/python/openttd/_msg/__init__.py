#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module declares the work functions for incoming messages.

These are defined in C++, so openttd._util takes the content of this module
and sets Msg::NAME.work to openttd._msg.NAME,
"""

from __future__ import annotations

# submodules use '__all__' for selectively exporting things …
from .command import *

# … but this module itself does not (fiddling with '__all__' is frowned upon)
# thus we resort to underscoring.
from typing import Awaitable as _Avaitable, Never as _Never


def Start(self,main) -> None:
    main.debug(2,"Python start completed.")

def ConsoleCmd(self,main) -> None:
    return main.handle_command(self)

def CommandRun(self,main) -> None:
    return main.handle_run(self)

def ModeChange(self,main) -> _Awaitable:
    return main.set_game_mode(self.mode)

def PauseState(self,main) -> _Awaitable:
    return main.set_pause_state(self.paused)

def Stop(self,main) -> _Never:
    raise RuntimeError("This message must be caught earlier!")

