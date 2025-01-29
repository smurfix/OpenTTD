/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/msg_command.hpp"
#include "network/network.h"
#include "network/network_internal.h"

#pragma GCC diagnostic ignored "-Wcast-function-type"

extern CommandCallbackData CcGame;

namespace PyTTD::Msg {

	CmdRelay::CmdRelay(Commands cmd, const CommandDataBuffer &data, CompanyID company // , CommandCallbackData *callback
	) : command(new CommandPacket() //, callback(callback)
	) {
		command->cmd = cmd;
		command->data = data;
		command->company = company;
		command->callback = (CommandCallback *)&CcGame; // Yes this is annoying

		command->my_cmd = true;
		command->err_msg = 0;
	}

	void CmdRelay::Process() {
		if(! _networking) {
			UnsafeCallCmd(*command);
		} else {
			NetworkSendCommand(command->cmd, command->err_msg, (CommandCallback *) &CcGame // CcPython
			, command->company, command->data);
		}

		_current_company = _local_company;
	}
}
