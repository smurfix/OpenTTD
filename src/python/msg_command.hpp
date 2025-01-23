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
#include "instance.hpp"
#include "network/network_internal.h"

namespace PyTTD::Msg {
	// Send a command to OpenTTD for execution
	class NB_IMPORT CmdRelay : public MsgBase {
	public:
		CmdRelay(const CommandData &data, CompanyID company);

		inline Commands GetCmd() { return (Commands)command->cmd; }
		inline const TileIndex &GetTile() { return command->tile; }
		inline const uint32_t &GetP1() { return command->p1; }
		inline const uint32_t &GetP2() { return command->p2; }
		inline const uint64_t &GetP3() { return command->p3; }
		inline const std::string *GetText() { return new std::string{command->text}; }
		inline CompanyID GetCompany() { return command->company; }
	private:
		CommandPacketPtr command;

		void Process() override;
	};

	// send a completed command to Python
	class CmdResult : public MsgBase {
	public:
		CmdResult(const CommandCost &result, TileIndex tile, uint32_t p1,uint32_t p2, uint64_t p3, Commands cmd)
			: cmd(cmd), result(result), tile(tile), p1(p1), p2(p2), p3(p3) {}

		inline const Commands &GetCmd() { return cmd; }
		inline const TileIndex &GetTile() { return tile; }
		inline const uint32_t &GetP1() { return p1; }
		inline const uint32_t &GetP2() { return p2; }
		inline const uint64_t &GetP3() { return p3; }
		inline const CommandCost &GetResult() { return result; }
	private:
		Commands cmd;
		CommandCost result;
		TileIndex tile;
		uint32_t p1;
		uint32_t p2;
		uint64_t p3;
	};

	// send a completed command to Python
	class CmdResult2 : public MsgBase {
	public:
		CmdResult2(const CommandCost &result, TileIndex tile, uint32_t p1, uint32_t p2, uint64_t p3, Commands cmd, CompanyID company)
			: cmd(cmd), result(result), tile(tile), p1(p1), p2(p2), p3(p3), company(company) {}

		inline Commands GetCmd() { return cmd; }
		inline TileIndex GetTile() { return tile; }
		inline const uint32_t &GetP1() { return p1; }
		inline const uint32_t &GetP2() { return p2; }
		inline const uint64_t &GetP3() { return p3; }
		inline CommandCost GetResult() { return result; }
		inline CompanyID GetCompany() { return company; }
	private:
		Commands cmd;
		CommandCost result;
		TileIndex tile;
		uint32_t p1;
		uint32_t p2;
		uint64_t p3;
		CompanyID company;
	};

	// Log command execution to Python
	class CmdTrace : public MsgBase {
	public:
		CmdTrace(Commands cmd, const CommandCost &result, TileIndex tile, uint32_t p1, uint32_t p2, uint64_t p3, CompanyID company)
			: cmd(cmd), result(result), tile(tile), p1(p1), p2(p2), p3(p3), company(company) {}

		inline const Commands &GetCmd() { return cmd; }
		inline TileIndex GetTile() { return tile; }
		inline const uint32_t &GetP1() { return p1; }
		inline const uint32_t &GetP2() { return p2; }
		inline const uint64_t &GetP3() { return p3; }
		inline const CommandCost &GetResult() { return result; }
		inline CompanyID GetCompany() { return company; }
	private:
		Commands cmd;
		CommandCost result;
		TileIndex tile;
		uint32_t p1;
		uint32_t p2;
		uint64_t p3;
		CompanyID company;
	};
}

#endif /* PY_MSG_COMMAND_H */
