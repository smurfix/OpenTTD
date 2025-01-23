/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/task.hpp"

#include "nanobind/nanobind.h"
#include "nanobind/stl/string.h"
#include "nanobind/stl/vector.h"

#include "python/msg_base.hpp"
#include "python/msg_console.hpp"
#include "python/msg_command.hpp"
#include "python/msg_mode.hpp"

#include "company_type.h"

#include "safeguards.h"

namespace py = nanobind;

namespace PyTTD {
	using namespace Msg;
	using namespace nanobind::literals;

	void init_ttd_msg(py::module_ &mg)
	{
		auto m = mg.def_submodule("msg", "Message support");

		py::class_<MsgBase>(m, "_Msg", py::dynamic_attr());

		/* msg_base */
		py::class_<Msg::Start, MsgBase>(m, "Start", py::dynamic_attr())
			.def(py::new_(&NewMsg<Msg::Start>));
		py::class_<Msg::Stop, MsgBase>(m, "Stop", py::dynamic_attr())
			.def(py::new_(&NewMsg<Msg::Stop>));

		/* msg_console */
		py::class_<Msg::ConsoleCmd, MsgBase>(m, "ConsoleCmd", py::dynamic_attr())
			.def_prop_ro("args", &ConsoleCmd::GetArgs);
		py::class_<Msg::ConsoleMsg, MsgBase>(m, "ConsoleMsg", py::dynamic_attr())
			.def(py::new_(&NewMsg<Msg::ConsoleMsg, std::string>), "text"_a)
			.def_prop_ro("text", &ConsoleMsg::GetText)
			;

		/* msg_mode */
		py::class_<Msg::ModeChange, MsgBase>(m, "ModeChange", py::dynamic_attr())
			.def_prop_ro("mode", &ModeChange::GetMode);
		py::class_<Msg::PauseState, MsgBase>(m, "PauseState", py::dynamic_attr())
			.def_prop_ro("paused", &PauseState::GetState);

		/* msg_command */
		py::class_<Msg::CmdRelay, MsgBase>(m, "CmdRelay", py::dynamic_attr())
			.def(py::new_([](const CommandData &cmd, CompanyID company){
				return new Msg::CmdRelay(cmd, company);
			}));

		py::class_<Msg::CmdResult, MsgBase>(m, "CmdResult", py::dynamic_attr())
			.def_prop_ro("cmd", &CmdResult::GetCmd)
			.def_prop_ro("tile", &CmdResult::GetTile)
			.def_prop_ro("p1", &CmdResult::GetP1)
			.def_prop_ro("p2", &CmdResult::GetP2)
			.def_prop_ro("p3", &CmdResult::GetP3)
			.def_prop_ro("result", &CmdResult::GetResult)
			;
		py::class_<Msg::CmdResult2, MsgBase>(m, "CmdResult2", py::dynamic_attr())
			.def_prop_ro("cmd", [](CmdResult2 &x){ return (Commands)(CMD_ID_MASK & (uint32_t)x.GetCmd()); })
			.def_prop_ro("flags", [](CmdResult2 &x){ return (FlaggedCommands)(CMD_FLAGS_MASK & (uint32_t)x.GetCmd()); })
			.def_prop_ro("tile", &CmdResult2::GetTile)
			.def_prop_ro("p1", &CmdResult2::GetP1)
			.def_prop_ro("p2", &CmdResult2::GetP2)
			.def_prop_ro("p3", &CmdResult2::GetP3)
			.def_prop_ro("result", &CmdResult2::GetResult)
			.def_prop_ro("company", &CmdResult2::GetCompany)
			;
		py::class_<Msg::CmdTrace, MsgBase>(m, "CmdTrace", py::dynamic_attr())
			.def_prop_ro("cmd", &CmdTrace::GetCmd)
			.def_prop_ro("tile", &CmdTrace::GetTile)
			.def_prop_ro("p1", &CmdTrace::GetP1)
			.def_prop_ro("p2", &CmdTrace::GetP2)
			.def_prop_ro("p3", &CmdTrace::GetP3)
			.def_prop_ro("result", &CmdTrace::GetResult)
			;
	}
}
