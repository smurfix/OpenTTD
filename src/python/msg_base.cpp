/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/msg_base.hpp"
#include "python/task.hpp"
#include "safeguards.h"

#include "nanobind/nanobind.h"

namespace py = nanobind;

namespace PyTTD {

	void Msg::Start::Process() {
	}

	void Msg::Stop::Process() {
		Task::Stop();
	}

	void init_ttd_msg(py::module_ &mg)
	{
		auto m = mg.def_submodule("msg", "Message support");

		py::class_<MsgBase>(m, "_Msg", py::dynamic_attr());

		py::class_<Msg::Start, MsgBase>(m, "Start", py::dynamic_attr())
			.def(py::init<>());
		py::class_<Msg::Stop, MsgBase>(m, "Stop", py::dynamic_attr())
			.def(py::init<>());

	}
}
