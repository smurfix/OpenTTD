/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/task.hpp"
#include "safeguards.h"

#include "nanobind/nanobind.h"
#include "nanobind/stl/string.h"
#include "nanobind/stl/vector.h"

#include "python/msg_base.hpp"
#include "python/msg_console.hpp"
#include "python/msg_mode.hpp"

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
			.def(py::new_(&NewMsg<Msg::ConsoleMsg, std::string>), "text"_a);

		/* msg_mode */
		py::class_<Msg::ModeChange, MsgBase>(m, "ModeChange", py::dynamic_attr())
			.def_prop_ro("mode", &ModeChange::GetMode);
		py::class_<Msg::PauseState, MsgBase>(m, "PauseState", py::dynamic_attr())
			.def_prop_ro("paused", &PauseState::GetState);

	}
}
