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

#include "python/wrap.hpp"

#include "script/api/script_object.hpp"
#include "script/script_storage.hpp"

namespace PyTTD {
	LockGame::LockGame()
		: storage(Storage::from_python())
		, unlock()
		, drv(reinterpret_cast<VDriver *>(VDriver::GetInstance()))
		, lock(drv->GetStateMutex())
		, framerate(PFE_PYTHON)
		, active(&instance)
		, storage_set(instance,storage)
		, mode()
		, cur_company(_current_company)
	{
		cur_company.Change(instance.py_storage->company);
	}

	LockGame::~LockGame()
	{
		cur_company.Restore();
	}

	// command hook
	py::object cmd_hook(CommandDataPtr cb)
	{
		static py::object cbfn;

		if(! cbfn) {
			py::module_ ttd = py::module_::import_("_ttd");
			cbfn = ttd.attr("_command_hook");
		}
		py::object cbd = py::cast<CommandDataPtr>(std::move(cb));
		return cbfn(cbd);
	}

}
