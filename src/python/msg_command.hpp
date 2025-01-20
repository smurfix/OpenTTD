/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_MSG_MODE_H
#define PY_MSG_MODE_H

#include "python/msg_base.hpp"
#include "openttd.h"


namespace PyTTD::Msg {
	// Send the command to Python
	class CmdRelay : public MsgBase {
	public:
		CmdRelay(Commands cmd, const CommandDataBuffer &data)
			: cmd(cmd), data(data) {}

		inline const Commands &GetCmd() { return cmd; }
		inline const CommandDataBuffer &GetData() { return data; }
	private:
		Commands cmd;
		CommandDataBuffer data;
	};

	class _CmdResult : public MsgBase {
	public:
		_CmdResult(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, const CommandDataBuffer &result_data)
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

	// send a completed command to Python
	class CmdResult : public _CmdResult {
	public:
		CmdResult(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, const CommandDataBuffer &result_data) : _CmdResult(cmd,result,data,result_data){}
	};

	// Log command execution to Python
	class CmdTrace : public _CmdResult {;
		CmdTrace(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, const CommandDataBuffer &result_data) : _CmdResult(cmd,result,data,result_data){}
	};
}

#endif
