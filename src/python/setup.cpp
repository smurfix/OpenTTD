/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>

#include <nanobind/nanobind.h>
#include <nanobind/stl/map.h>

#include "script/api/script_controller.hpp"

namespace py = nanobind;

namespace PyTTD {
	extern void init_ttd_msg(py::module_ &);
	extern void init_ttd_enums(py::module_ &);
	extern void init_ttd_object(py::module_ &);
	extern void init_ttd_support(py::module_ &);
	extern void init_ttd_modules(py::module_ &);
	extern void init_ttd_string_id(py::module_ &);

	PyObject *init_ttd()
	{
		// magic incantation from nanobind sources
		static PyModuleDef ttd_def;
		py::detail::init(nullptr);
		py::module_ m = py::steal<py::module_>(py::detail::module_new("_ttd",&ttd_def));

		init_ttd_object(m);
		init_ttd_support(m);
		init_ttd_msg(m);
		init_ttd_enums(m);
		init_ttd_modules(m);
		init_ttd_string_id(m);

		// magic incantation 2
		return m.release().ptr();
	}

	void exit_ttd()
	{
		py::dict mods = py::module_::import_("sys").attr("modules");
		mods.attr("__delitem__")("_ttd");
	}

}
