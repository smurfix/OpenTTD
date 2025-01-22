/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>

#include "python/object.hpp"
#include "python/task.hpp"

#include "script/api/script_object.hpp"
#include "script/script_instance.hpp"
#include "script/api/script_text.hpp"
#include "script/api/script_date.hpp"
#include "script/api/script_controller.hpp"

namespace PyTTD {
	namespace py = nanobind;

	void init_ttd_support(py::module_ &mg) {
		auto m = mg.def_submodule("support", "Various supporting classes and enums");

		m.def("get_tick", &ScriptController::GetTick);
		m.def("set_command_delay", &ScriptController::SetCommandDelay);
		m.def("get_setting", &ScriptController::GetSetting, nanobind::arg("name"));
		m.def("get_version", &ScriptController::GetVersion);
		m.def("print", &ScriptController::Print);

		py::enum_<Owner>(m, "Owner", py::is_flag())
			.value("BEGIN",OWNER_BEGIN)
			.value("INVALID",INVALID_OWNER)
			.value("MAX_COMPANIES",MAX_COMPANIES)
			.value("NEW",COMPANY_NEW_COMPANY)
			.value("SPECTATOR",COMPANY_SPECTATOR)
			.value("NONE",OWNER_NONE)
			.value("WATER",OWNER_WATER)
			.value("DEITY",OWNER_DEITY)
			.value("INACTIVE",COMPANY_INACTIVE_CLIENT)
			// .export_values()
			;

		py::class_<TileIndex>(m, "Tile_")
			.def(py::init_implicit<uint32_t>())
			.def(py::new_([](unsigned int xy){ return TileIndex(xy);}))
			.def(py::new_([](unsigned int x, unsigned int y){ return TileXY(x,y);}))
			.def("__int__", [](const TileIndex &t){ return t.value; })
			.def("__repr__", [](const TileIndex &t){ return fmt::format("Tile({})", t.value);})
			.def("__str__", [](const TileIndex &t){ return fmt::format("Tile({},{})", TileX(t), TileY(t));})
			;

		m.attr("INVALID_TILE") = INVALID_TILE;

		py::class_<Money>(m, "Money")
			.def(py::init_implicit<int64_t>())
			.def("__int__", [](const Money &x){ return (int64_t)x;})
			.def("__add__", [](const Money &x, const Money &y){ return (int64_t)(x+y);})
			.def("__add__", [](const Money &x, const int64_t &y){ return (int64_t)(x+Money{y});})
			.def("__sub__", [](const Money &x, const Money &y){ return (int64_t)(x-y);})
			.def("__sub__", [](const Money &x, const int64_t &y){ return (int64_t)(x-Money{y});})
			.def("__mul__", [](const Money &x, const int64_t &y){ return Money{x*y};})
			.def("__div__", [](const Money &x, const int64_t &y){ return Money{x*y};})
			.def("__repr__", [](const Money &x){ return fmt::format("Money({})", (int64_t)x);})
			.def("__str__", [](const Money &x){ return fmt::format("€ {}", (int64_t)x);})
			;

		py::enum_<ScriptDate::Date>(m, "Date", py::is_arithmetic())
			.value("INVALID", ScriptDate::Date::DATE_INVALID)
			// .export_values()
			;

		py::class_<Text>(m, "_Text");
		py::class_<RawText, Text>(m, "Text")
			.def(py::new_([](std::string s) {
				auto res = new RawText(s);
				res->AddRef();
				return res;
			}))
			.def(py::init<std::string>())
			.def("__str__", &RawText::GetEncodedText)
			.def("__del__", &SimpleCountedObject::Release)
			;
	}

}
