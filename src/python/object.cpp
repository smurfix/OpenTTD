/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>
#include <nanobind/intrusive/counter.h>

#include <iostream>
#include <memory>
#include "debug.h"

#include "python/object.hpp"
#include "python/instance.hpp"
#include "python/task.hpp"
#include "python/call_py.hpp"

#include "script/api/script_object.hpp"
#include "script/script_storage.hpp"

#include <nanobind/intrusive/counter.inl>

namespace PyTTD {
	namespace py = nanobind;
	void init_ttd_object(py::module_ &mg)
	{
		auto m = mg.def_submodule("object", "ScriptObject support");

		py::intrusive_init(
			[](PyObject *o) noexcept {
				py::gil_scoped_acquire guard;
				Py_INCREF(o);
			},
			[](PyObject *o) noexcept {
				py::gil_scoped_acquire guard;
				Py_DECREF(o);
			});

		py::class_<SimpleCountedObject>(m, "SimpleCountedObject",
			py::intrusive_ptr<SimpleCountedObject>(
				[](SimpleCountedObject *o, PyObject *po) noexcept { o->set_self_py(po); }));
		py::class_<ScriptObject, SimpleCountedObject>(m, "ScriptObject");

		py::class_<Script>(m, "Script")
			.def_rw("id", &Script::id)
			.def_rw("cls", &Script::class_)
			.def_rw("info", &Script::info)
			.def_rw("company", &Script::company)
			;

		py::class_<Storage>(m, "Storage")
			.def(py::new_(&Storage::Create))
			.def_rw("company", &Storage::company)
			.def_ro("root_company", &Storage::root_company)
			.def_rw("allow_do_command", &Storage::allow_do_command)
			.def_rw("costs", &Storage::costs)

			.def_rw("last_cmd", &Storage::last_cmd)
			.def_prop_rw("last_data",
					[](const Storage &x) {
						auto &d = x.last_data;
						return py::bytes((const uint8_t *)d.data(),d.size());
					},
					[](Storage &x, py::bytes d) {
						auto &ld = x.last_data;
						ld.assign((const uint8_t *)d.data(),((const uint8_t *)d.data())+d.size());
					})
			.def_rw("last_result", &Storage::last_command_res)
			.def_prop_rw("last_result_data",
					[](const Storage &x) {
						auto &d = x.last_cmd_ret;
						return py::bytes((const uint8_t *)d.data(),d.size());
					},
					[](Storage &x, py::bytes d) {
						auto &ld = x.last_cmd_ret;
						ld.assign((const uint8_t *)d.data(),((const uint8_t *)d.data())+d.size());
					})

			.def_rw("last_cost", &Storage::last_cost)
			.def_rw("last_error", &Storage::last_error)

			.def_rw("road_type", &Storage::road_type)
			.def_rw("rail_type", &Storage::rail_type)

			.def_prop_rw("result", &Storage::get_result, &Storage::add_result, "Read the command result data")
			;
		py::class_<Task>(m, "Task")
			.def("stop", &Task::PyStop, "Stop the Python task")
			.def("wait", &Task::PyWaitNewMsg, "Wait for new messages")
			.def("send", &Task::PySend, "Send a message")
			.def("recv", &Task::PyRecv, "Read the next message")
			;

		// intentionally not in a submodule
		mg.def("debug", [](int level, const char *text) { Debug(python, level, "{}", text); }, "Debug logging ('python')");
	}

	// data hook
	StoragePtr Storage::from_python()
	{
		static py::object cbfn;
		py::gil_scoped_acquire lock;

		if(! cbfn) {
			py::module_ ttd = py::module_::import_("_ttd");
			cbfn = ttd.attr("_storage_hook");
		}
		return py::cast<StoragePtr>(cbfn());
	}

	py::object Storage::get_result()
	{
		auto val = cmd_result;
		cmd_result = py::none();
		return val;
	}
	void Storage::add_result(py::object obj)
	{
		if (cmd_result.is_none())
			cmd_result = py::list();
		py::cast<py::list>(cmd_result).append(obj);
	}
}
