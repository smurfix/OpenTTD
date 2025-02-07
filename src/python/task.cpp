/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <Python.h>
#include <osdefs.h>  // for DELIM

#include <nanobind/nanobind.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/vector.h>

#include "python/task.hpp"
#include "python/queues.hpp"
#include "python/call_py.hpp"
#include "python/setup.hpp"
#include "python/msg_base.hpp"
#include "python/msg_console.hpp"
#include "python/msg_mode.hpp"

#include "stdafx.h"
#include "debug.h"
#include "fileio_func.h"
#include "framerate_type.h"
#include "console_func.h"
#include "command_type.h"
#include "network/network_internal.h"
#include "core/backup_type.hpp"

#include <string>
#include <memory>
#include <thread>
#include <iostream>
#include <sstream>
#include <format>
#include <vector>


namespace py = nanobind;

// helper to split a string
std::vector<std::string> split (const std::string &s, char delim) {
    std::vector<std::string> result;
    std::stringstream ss (s);
    std::string item;

    while (getline (ss, item, delim)) {
		if (item.size())
			result.push_back (item);
    }

    return result;
}

#ifdef DELIM
#undef DELIM
#endif

#ifdef MS_WINDOWS
static const char DELIM = ';';
#else
static const char DELIM = ':';
#endif

namespace PyTTD {
	std::unique_ptr<Task> Task::current = nullptr;

	void Task::_PyRunner()
	{
		// TODO use a subinterpreter with py3.12+
		Debug(python, 3, "In Python thread");
		PyStatus status;

		std::wstring prog_name = L"openttd::Python";

		PyConfig cfg;
		PyConfig_InitIsolatedConfig(&cfg);
		cfg.bytes_warning=1;
		cfg.faulthandler=1;
		cfg.use_environment=1;
		cfg.user_site_directory=1;

		cfg.module_search_paths_set = 0;

		status = PyConfig_SetString(&cfg, &cfg.program_name, prog_name.c_str());
		if (PyStatus_Exception(status))
			goto exc;
		status = PyConfig_SetString(&cfg, &cfg.run_filename, prog_name.c_str());
		if (PyStatus_Exception(status))
			goto exc;

		cfg.quiet=1;
		if(true) {
			PyImport_AppendInittab("_ttd", &init_ttd);

			status = Py_InitializeFromConfig(&cfg);
			if (PyStatus_Exception(status) != 0) {
				PyConfig_Clear(&cfg);
				throw std::runtime_error(PyStatus_IsError(status) != 0 ? status.err_msg : "Failed to init CPython");
			}
			PyConfig_Clear(&cfg);

			try {
				py::module_ sys_ = py::module_::import_("sys");
				py::list m_ = sys_.attr("path").attr("insert");

				// Python does have a native way to set up the
				// interpreter's paths, it's based on wide-char
				// strings and thus a major hassle to use.

				int i = 0;
				char *env = getenv("TTDPYTHONPATH");
				if (env != nullptr && *env) {
					for (auto s : split(env, DELIM)) {
						m_(i,s);
						i += 1;
					}
				}
				for (auto sp : _searchpaths) {
					std::string sps = sp;
					sps += PATHSEP;
					sps += "python";

					m_(i,sps);
					i += 1;
				}

				Debug(python, 4, "Importing _ttd module");
				nanobind::module_ ttd = nanobind::module_::import_("_ttd");
				Debug(python, 4, "Setting task var");
				ttd.attr("_task") = this;

				ttd.attr("debug_level") = _debug_python_level;

				Debug(python, 4, "Loading openttd._main");
				nanobind::module_ ottd = nanobind::module_::import_("openttd._main");
				ottd.attr("run")();

				Debug(python, 2, "Python task ends.");
			}
			catch (const std::exception &ex) {
				std::cerr << "*** The Python interpreter died ***" << std::endl;
				std::cerr << typeid(ex).name() << std::endl;
				std::cerr << "  what(): " << ex.what() << std::endl;
			}
			catch (...) {
				std::cerr << "*** The Python interpreter died ***" << std::endl;
				std::cerr << typeid(std::current_exception()).name() << std::endl;
				throw;
			}

			PyTTD::exit_ttd();
			Py_Finalize();

		} else {
	exc:
			Debug(python, 1, "Python start failed (external)");
			PyConfig_Clear(&cfg);
		}
		_Stop();
	}

	/**
	 * Mark the Python subsystem as stopped; sends a message
	 * that tells the Python message processor to terminate it.
	 */
	void Task::_Stop() {
		stopped = true;
		QueueToPy.send(NewMsg<Msg::Stop>());
	}

	/**
	 * Stops the Python subsystem.
	 *
	 * Called from Python.
	 */
	void Task::PyStop() {
		_Stop();
	}

	/**
	 * Start the Python subsystem.
	 */
	/* static */ void Task::Start(const std::string &main)
	{
		if (current) {
			Debug(python, 1, "Python thread already running");
			return;
		}

		Task::current = std::unique_ptr<Task>(new Task(main));
	}

	/**
	 * This starts the Python thread. Called from the constructor.
	 */
	void Task::_start(const std::string &main)
	{
		if (thread || !stopped) {
			Debug(python, 1, "Python thread already running");
			return;
		}

		Debug(python, 3, "Starting Python thread");
		stopped = false;

		std::unique_ptr<std::thread> thr = std::make_unique<std::thread>(&Task::_PyRunner, this);
		Task::thread = std::move(thr);

		QueueToPy.send(NewMsg<Msg::ModeChange>(_game_mode));
		QueueToPy.send(NewMsg<Msg::Start>());
		game_mode = _game_mode;

		if(main.size()) {
			QueueToPy.send(NewMsg<Msg::CommandRun>(main));
		}
	}

	/**
	 * Stop the Python thread.
	 *
	 * This function may only be called from OpenTTD.
	 */
	/* static */ void Task::Stop()
	{
		Debug(python, 3, "Python thread gets stopped");
		if (Task::current == nullptr)
			return;
		if(! current->stopped)
			current->_Stop();
		if (current->thread != nullptr) {
			current->thread->join();
			current->thread = nullptr;
		}
		current->stopped = true;
		current = nullptr;
		Debug(python, 2, "Python thread stopped.");
	}

	/***** Calls from OpenTTD *****/

// XXX this should probably be a template.
#define LOCK(if_dead)                       \
	if(!Task::IsRunning())                  \
		return (if_dead);                   \
                                            \
	nanobind::gil_scoped_acquire _acquire;  \
                                            \
	if(!Task::IsRunning())                  \
		return (if_dead);                   \

	/* static */ std::vector<unsigned int> Task::GetScriptIndices() {
		LOCK(std::vector<unsigned int>())
		try {
			nanobind::module_ ttd = nanobind::module_::import_("_ttd");
			py::object main = ttd.attr("_main");
			return py::cast<std::vector<unsigned int>>(main.attr("get_script_indices")());
		}
		catch (const std::exception &ex) {
			std::cerr << typeid(ex).name() << std::endl;
			std::cerr << "  what(): " << ex.what() << std::endl;
		}
		return std::vector<unsigned int>();
	}

	/* static */ bool Task::GetScriptInfo(unsigned int id, struct Script &data) {
		LOCK(false)
		try {
			nanobind::module_ ttd = nanobind::module_::import_("_ttd");
			py::object main = ttd.attr("_main");
			return py::cast<bool>(main.attr("get_script_info")(id, &data));
		}
		catch (const std::exception &ex) {
			std::cerr << typeid(ex).name() << std::endl;
			std::cerr << "  what(): " << ex.what() << std::endl;
		}
		return false;
	}

	/* static */ void Task::ProcessFromPython() {
		if(Task::current == nullptr) {
			PerformanceMeasurer::SetInactive(PFE_PYTHON);
			return;
		}
		if (Task::current->stopped) {
			PerformanceMeasurer::SetInactive(PFE_PYTHON);
			Task::Stop();
			return;
		}

		PerformanceMeasurer framerate(PFE_PYTHON);

		if (Task::current->game_mode != _game_mode) {
			Task::current->game_mode = _game_mode;
			Task::current->QueueToPy.send(NewMsg<Msg::ModeChange>(_game_mode));
		}
		if (Task::current->pause_state != _pause_mode) {
			Task::current->pause_state = _pause_mode;
			Task::current->QueueToPy.send(NewMsg<Msg::PauseState>(_pause_mode));
		}

		while(true) {
			if(Task::current == nullptr || Task::current->stopped)
				return;

			auto cmd = Task::current->QueueToTTD.recv();
			if (! cmd) {
				break;
			}
			cmd->Process();
		}
	}

	/* static */ void Task::ConsoleToPy(int argc, const char* const argv[])
	{
		if(Task::current == nullptr || Task::current->stopped) {
			IConsolePrint(CC_ERROR, "The Python task is not running.");
			return;
		}
		Task::current->QueueToPy.send(NewMsg<Msg::ConsoleCmd>(argc, argv));

	}

	/**
	 * Wait for the next message to Python.
	 * @param gen Generation counter.
	 * @return The generation counter for the next call to `wait_from_py`.
	 * @note Start with zero.
	 */
	uint32_t Task::PyWaitNewMsg(uint32_t counter)
	{
		if(current == nullptr || current.get() != this)
			throw std::domain_error("Not in current thread");

		{
			nanobind::gil_scoped_release _release;
			counter = QueueToPy.wait(counter);
		}

		if(Task::current == nullptr || current.get() != this)
			throw std::domain_error("Not in current thread");

		return counter;
	}

	/* static */ void Task::Send(MsgPtr msg)
	{
		if(!Task::IsRunning())
			return;
		Task::current->QueueToPy.send(std::move(msg));
	}

	void Task::PySend(MsgPtr msg)
	{
		QueueToTTD.send(std::move(msg));
	}

	MsgPtr Task::PyRecv()
	{
		return QueueToPy.recv();
	}
}

