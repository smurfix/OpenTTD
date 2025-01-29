/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_MSG_COMMAND_H
#define PY_MSG_COMMAND_H

#include <nanobind/nanobind.h>

#include "python/msg_base.hpp"
#include "python/object.hpp"

#include "openttd.h"
#include "command_type.h"
#include "network/network_internal.h"

namespace PyTTD::Msg {
	// Send a command to OpenTTD for execution
	class NB_IMPORT CmdRelay : public MsgBase {
	public:
		CmdRelay(Commands cmd, const CommandDataBuffer &data, CompanyID company //, CommandCallbackData *callback
		);

		CmdRelay(Commands cmd, py::bytes data, CompanyID company //, CommandCallbackData *callback
		) : CmdRelay(cmd, std::vector<uint8_t>((const uint8_t *)data.data(),((const uint8_t *)data.data())+data.size()), company //, callback
		) {}

		inline Commands GetCmd() { return command->cmd; }
		inline CommandDataBuffer GetData() { return command->data; }
		inline CompanyID GetCompany() { return command->company; }
		inline StringID GetErrMsg() { return command->err_msg; }
		inline CommandCallback *GetCallback() { return command->callback; }
		// inline CommandCallbackData *GetDataCallback() { return callback; }
	private:
		CommandPacketPtr command;
		// CommandCallbackData *callback;

		void Process() override;
	};

	// send a completed command to Python
	class CmdResult : public MsgBase {
	public:
		CmdResult(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, const CommandDataBuffer &result_data)
			: cmd(cmd), result(result), data(data), result_data(result_data) {}

		inline const Commands &GetCmd() const { return cmd; }
		inline const CommandCost &GetResult() const { return result; }
		inline const CommandDataBuffer &GetData() const { return data; }
		inline const CommandDataBuffer &GetResultData() const { return result_data; }
	private:
		Commands cmd;
		CommandCost result;
		CommandDataBuffer data;
		CommandDataBuffer result_data;
	};

	// send the completed data back
	class NB_IMPORT CmdResult3 : public MsgBase {
	public:
		CmdResult3(Commands cmd, const CommandCost &result, TileIndex tile, CompanyID company, py::object data) : cmd(cmd), result(result), tile(tile), company(company), data(data) {}

		inline Commands GetCmd() { return cmd; }
		inline CommandCost GetResult() { return result; }
		inline TileIndex GetTile() { return tile; }
		inline CompanyID GetCompany() { return company; }
		inline py::object GetData() { return data; }
	private:
		Commands cmd;
		CommandCost result;
		TileIndex tile;
		CompanyID company;
		py::object data;
	};

	// Log command execution to Python
	class CmdTrace : public MsgBase {
	public:
		CmdTrace(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, const CommandDataBuffer &result_data)
			: cmd(cmd), result(result), data(data), result_data(result_data) {}

		inline const Commands &GetCmd() { return cmd; }
		inline const CommandCost &GetResult() { return result; }
		inline const CommandDataBuffer &GetData() { return data; }
		inline const CommandDataBuffer &GetResultData() { return result_data; }
	private:
		Commands cmd;
		CommandCost result;
		CommandDataBuffer data;
		CommandDataBuffer result_data;
	};
}

#endif /* PY_MSG_COMMAND_H */
