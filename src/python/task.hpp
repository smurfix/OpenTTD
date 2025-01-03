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

#include <thread>
#include <memory>

namespace PyTTD {
	class Task {
	  public:
		Task() : stopped(true), QueueToPy(), QueueToTTD()
		{
			_start();
		}

		~Task() {
			Stop();
		}

		static bool IsRunning() { return current != nullptr && !current->stopped; }

		/**
		 * Process enqueued commands and messages from Python.
		 *
		 * Called as part of the game loop, by GameLoopSpecial.
		 */
		static void ProcessFromPython();

	  private:
		void _start();

	  public:
		/**
		 * Start the main Python task.
		 */
		static void Start();

		/**
		 * Stop the main Python task. Called from OpenTTD when exiting the game.
		 */
		static void Stop();

	  private:
		static std::unique_ptr<Task> current;

		std::unique_ptr<std::thread> thread;
		bool stopped;

		void _Stop();

		void _PyRunner();

		QToPy QueueToPy;
		LockedQ QueueToTTD;

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
