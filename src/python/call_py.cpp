/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>

#include "python/call_py.hpp"
#include "python/queues.hpp"
#include "python/task.hpp"

#include <exception>

namespace PyTTD {

	/**
	 * Start the Python subsystem
	 */
	void Start() {
		if (Task::IsRunning()) {
#ifdef NDEBUG
			return;
#else
			throw(std::logic_error("Python task is running"));
#endif
		}
		Task::Start();
	}

	/**
	 * Stop the Python subsystem
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
	 * Process the message queue from Python
	 */
	void ProcessFromPython() {
		Task::ProcessFromPython();
	}

	void ConsoleToPy(int argc, const char* const argv[]) {
		Task::ConsoleToPy(argc, argv);
	}
}
