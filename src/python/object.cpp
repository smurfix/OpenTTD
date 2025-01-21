/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/shared_ptr.h>

#include <iostream>
#include <memory>

#include "python/object.hpp"
#include "python/task.hpp"

#include "script/api/script_object.hpp"
#include "script/script_storage.hpp"

namespace PyTTD {
	namespace py = nanobind;
	void init_ttd_object(py::module_ &mg)
	{
		auto m = mg.def_submodule("object", "ScriptObject support");

		py::class_<SimpleCountedObject>(m, "SimpleCountedObject");
		py::class_<ScriptObject, SimpleCountedObject>(m, "ScriptObject");

		py::class_<Storage>(m, "Storage")
			.def(py::new_(&Storage::create))
			.def_rw("company", &Storage::company)
			.def_rw("real_company", &Storage::root_company)
			.def_rw("allow_do_command", &Storage::allow_do_command)
			.def_ro("costs", &Storage::costs)
			.def_ro("last_cost", &Storage::last_cost)
			.def_ro("last_error", &Storage::last_error)
			.def_ro("last_command_res", &Storage::last_command_res)
			.def_ro("last_data", &Storage::last_data)
			.def_ro("last_cmd", &Storage::last_cmd)
			.def_ro("last_cmd_ret", &Storage::last_cmd_ret)
			.def_ro("road_type", &Storage::road_type)
			.def_ro("rail_type", &Storage::rail_type)
			;
		py::class_<Task>(m, "Task")
			.def("stop", &Task::PyStop, "Stop the Python task")
			.def("wait", &Task::PyWaitNewMsg, "Wait for new messages")
			.def("send", &Task::PySend, "Send a message")
			.def("recv", &Task::PyRecv, "Read the next message")
			;

		// intentionally not in a submodule
		mg.def("debug", [](int level, const char *text) { Debug(python, level, "{}", text); },+ "Debug logging ('python')");
	}

	// If a call from Python to TTD generated a command,
	// we store it here.
	CommandContainerPtr currentCmd = nullptr;

#if 0
	static bool saveCmd(TileIndex tile, uint32_t p1, uint32_t p2, uint64_t p3, uint cmd, const std::string &text, const struct CommandAuxiliaryBase *aux_data, Script_SuspendCallbackProc *callback) {
		if(currentCmd)
			throw std::domain_error("Second command");
		currentCmd.reset(new CommandContainer());
		currentCmd->cmd = cmd;
		currentCmd->p1 = p1;
		currentCmd->p2 = p2;
		currentCmd->p3 = p3;
		currentCmd->tile = tile;
		currentCmd->text = text;
		return true;
	}
#endif
	// command hook
	py::object cmd_hook(CommandContainerPtr cb)
	{
		static py::object cbfn;

		if(! cbfn) {
			py::module_ ttd = py::module_::import_("_ttd");
			cbfn = ttd.attr("_command_hook");
		}
		return cbfn(cb);
	}

	// data hook
	StoragePtr Storage::from_python()
	{
		static py::object cbfn;

		if(! cbfn) {
			py::module_ ttd = py::module_::import_("_ttd");
			cbfn = ttd.attr("_storage_hook");
		}
		return py::cast<StoragePtr>(cbfn());
	}

}
