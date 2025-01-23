/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/msg_command.hpp"
#include "network/network.h"
#include "network/network_internal.h"
#include "command_func.h"
#include "company_func.h"

extern ClientID _cmd_client_id;

extern void CcPython(const CommandCost &result, TileIndex tile, uint32_t p1, uint32_t p2, uint64_t p3, uint32_t cmd);

namespace PyTTD::Msg {

	CmdRelay::CmdRelay(const CommandData &d, CompanyID company) : command(CommandPacketPtr(new CommandPacket())) {

		command->cmd = d.cmd;
		command->tile = d.tile;
		command->p1 = d.p1;
		command->p2 = d.p2;
		command->p3 = d.p3;
		command->text = d.text;
		command->aux_data = d.aux_data;
		command->company = company;

		command->my_cmd = true;
		command->callback = &CcPython;
	}

	void CmdRelay::Process() {
		if(! _networking) {
			UnsafeCallCmd(*command);
		} else {
			NetworkSendCommand(command->tile, command->p1, command->p2, command->p3, command->cmd, &CcPython, command->text.c_str(), command->company, &*command->aux_data);
		}

		_current_company = _local_company;
		_cmd_client_id = INVALID_CLIENT_ID;
	}
}
