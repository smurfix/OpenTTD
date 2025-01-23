#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from openttd._main import CmdR

def CmdResult(self,main):
    cmdr = CmdR(cmd=self.cmd, data=self.data, company=self.company)
    return main.handle_result(cmdr)

def CmdResult2(self,main):
    return main.handle_result2(self)

def CmdTrace(self,main):
    return main.trace_command(self)
