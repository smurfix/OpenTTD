/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>

#include "command_type.h"
#include "framerate_type.h"
#include "python/call_py.hpp"
#include "python/queues.hpp"
#include "python/task.hpp"

#include "nanobind/nanobind.h"
#include "nanobind/stl/vector.h"

#include <exception>
#include <iostream>

namespace py = nanobind;

namespace PyTTD {

	/**
	 * Start the Python subsystem
	 */
	void Start(const std::string &main) {
		if (Task::IsRunning()) {
#ifdef NDEBUG
			return;
#else
			throw(std::logic_error("Python task is running"));
#endif
		}
		Task::Start(main);
	}

	/**
	 * Stop the Python subsystem.
	 */
	void Stop() {
		Task::Stop();
	}

	/**
	 * Check if the Python subsystem is up
	 */
	bool IsRunning() {
		return Task::IsRunning();
	}

	/**
	 * Retrieve the IDs of currently-)running scripts.
	 */
	std::vector<unsigned int> Script::GetIndices() {
		return Task::GetScriptIndices();
	}

	/**
	 * Retrieve information about a script.
	 *
	 * Caution: the data is returned via a static buffer and thus
	 * needs to be copied out before the next call to this function.
	 */
	Script *Script::GetIfValid(unsigned int id)
	{
		static Script res;
		return Task::GetScriptInfo(id, res) ? &res : nullptr;
	}

	/**
	 * Process the message queue from Python
	 */
	void ProcessFromPython() {
		Task::ProcessFromPython();
	}

	void ConsoleToPy(int argc, const char* const argv[]) {
		Task::ConsoleToPy(argc, argv);
	}

	bool CheckPending(Commands cmd, const CommandDataBuffer &data)
	{
		PerformanceMeasurer framerate(PFE_PYTHON);
		nanobind::gil_scoped_acquire _acquire;
		py::bytes buf{data.data(),data.size()};
		try {
			nanobind::module_ ttd = nanobind::module_::import_("_ttd");
			py::object main = ttd.attr("_main");
			return py::cast<bool>(main.attr("check_pending")(cmd, buf));
		} catch (const std::exception &ex) {
			std::cerr << typeid(ex).name() << std::endl;
			std::cerr << "  what(): " << ex.what() << std::endl;

			return false;
		}
		return false;
	}

}
