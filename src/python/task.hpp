/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_TASK_H
#define PY_TASK_H

#include <nanobind/nanobind.h>

#include "python/queues.hpp"

#include "company_type.h"
#include "openttd.h"

#include <thread>
#include <memory>

namespace PyTTD {
	class Task {
	  public:
		Task(const std::string &main) : stopped(true), QueueToPy(), QueueToTTD()
		{
			_start(main);
		}

		~Task() {
			Stop();
		}

		/**
		 * Process enqueued commands and messages from Python.
		 *
		 * Called as part of the game loop, by GameLoopSpecial.
		 */
		static void ProcessFromPython();

		/**
		 * Forward console commands to Python.
		 */
		static void ConsoleToPy(int argc, const char* const argv[]);

	  private:
		void _start(const std::string &);

		GameMode game_mode = GM_BOOTSTRAP;
		PauseMode pause_state = PM_PAUSED_ERROR;  // initial nonsense(we hope) state

	  public:
		/**
		 * Start the main Python task.
		 */
		static void Start(const std::string &);

		/**
		 * Tell the main Python task to stop (and wait for it to do so).
		 */
		static void Stop();

		/**
		 * Test whether the Python task is running.
		 */
		static bool IsRunning() { return current != nullptr && !current->stopped; }

		/**
		 * Send a message to Python.
		 */
	 	static void Send(MsgPtr msg);

		/**
		 * Retrieve the IDs of currently-)running scripts.
		 */
		static std::vector<unsigned int> GetScriptIndices();

		/**
		 * Retrieve information about a script.
		 */
		static bool GetScriptInfo(unsigned int id, struct Script &data);

	  private:
		static std::unique_ptr<Task> current;

		std::unique_ptr<std::thread> thread;
		bool stopped;

		void _Stop();

		void _PyRunner();

		QToPy QueueToPy;
		QToTTD QueueToTTD;

	 public:
		/**
		 * Stop the main Python task. Called from Python when the
		 * interpreter ends.
		 */
		void PyStop();

		/**
		 * Send a message from Python
		 */
	 	void PySend(MsgPtr msg);

		/**
		 * Retrieve the next message for Python
		 */
	 	MsgPtr PyRecv();

		/**
		 * Block a Python tread until the next message arrives
		 */
		uint32_t PyWaitNewMsg(uint32_t counter);
	};
}

#endif
