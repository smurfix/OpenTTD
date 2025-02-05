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
#include "python/instance.hpp"
#include "python/wrap.hpp"

#include "company_type.h"

#include "safeguards.h"

namespace py = nanobind;

namespace PyTTD {
	using namespace Msg;
	using namespace nanobind::literals;

	void init_ttd_msg(py::module_ &mg)
	{
		auto m = mg.def_submodule("msg", "Messaging and callback support");

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

		/* msg_console */
		py::class_<Msg::CommandRun, MsgBase>(m, "CommandRun", py::dynamic_attr())
			.def_prop_ro("msg", &CommandRun::GetMsg);
		py::class_<Msg::CommandRunEnd, MsgBase>(m, "CommandRunEnd", py::dynamic_attr())
			.def(py::new_(&NewMsg<Msg::CommandRunEnd, std::string>), "res"_a)
			.def_prop_ro("msg", &CommandRunEnd::GetMsg)
			;

		/* msg_mode */
		py::class_<Msg::ModeChange, MsgBase>(m, "ModeChange", py::dynamic_attr())
			.def_prop_ro("mode", &ModeChange::GetMode);
		py::class_<Msg::PauseState, MsgBase>(m, "PauseState", py::dynamic_attr())
			.def_prop_ro("paused", &PauseState::GetState);

		/* msg_command */
		py::class_<Msg::CmdRelay, MsgBase>(m, "CmdRelay", py::dynamic_attr())
			.def(py::new_([](
				Commands cmd,
				py::bytes data,
				CompanyID company)
				//intptr_t callback)
				 { return new Msg::CmdRelay(cmd,data,company);}), // ,(CommandCallbackData *)callback);}),
				py::arg("cmd"),
				py::arg("data"),
				py::arg("company"));
				//py::arg("callback"));

		py::class_<Msg::CmdResult, MsgBase>(m, "CmdResult", py::dynamic_attr())
			.def_prop_ro("cmd", &CmdResult::GetCmd)
			.def_prop_ro("data", [](const CmdResult &x) {
				auto d = x.GetData();
				return py::bytes(d.data(),d.size());
			})
			.def_prop_ro("result", &CmdResult::GetResult)
			.def_prop_ro("resultdata", [](const CmdResult &x) {
				auto d = x.GetResultData();
				return py::bytes(d.data(),d.size());
			})
			;
		py::class_<Msg::CmdResult3, MsgBase>(m, "CmdResult3", py::dynamic_attr())
			.def_prop_ro("cmd", &CmdResult3::GetCmd)
			.def_prop_ro("result", &CmdResult3::GetResult)
			.def_prop_ro("company", &CmdResult3::GetCompany)
			.def_prop_ro("tile", &CmdResult3::GetTile)
			.def_prop_ro("data", &CmdResult3::GetData)
			;
		py::class_<Msg::CmdTrace, MsgBase>(m, "CmdTrace", py::dynamic_attr())
			.def_prop_ro("cmd", &CmdTrace::GetCmd)
			.def_prop_ro("data", &CmdTrace::GetData)
			.def_prop_ro("result", &CmdTrace::GetResult)
			.def_prop_ro("resultdata", &CmdTrace::GetResultData)
			;

		m.def("_done_cb", []( intptr_t callback, StoragePtr storage ){
			typedef void (*callback_t)(ScriptInstance *) ;
			callback_t cb = (callback_t)callback;

			CommandDataPtr cmd = nullptr;
			auto state = PyEval_SaveThread();
			{
				LockGame lock(storage);
				(*cb)(&instance);
			}
			cmd = std::move(instance.currentCmd);
			PyEval_RestoreThread(state);
			if (cmd)
				return cmd_hook(std::move(cmd));
			return py::none();
		});
	}
}
