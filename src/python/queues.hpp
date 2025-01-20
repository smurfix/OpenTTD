/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_QUEUES_H
#define PY_QUEUES_H

#include "python/msg_base.hpp"

#include <queue>
#include <mutex>
#include <condition_variable>

namespace PyTTD {

	// just an abbreviation
	template<typename T>
	using ptr = std::unique_ptr<T>;

	/**
	 * A basic queue for messages, protected with a lock.
	 */
	class LockedQ {
	public:
		NB_IMPORT LockedQ() {}
		~LockedQ() = default;

	protected:
		std::mutex lock;

	private:
		std::queue<MsgPtr> queue;

	public:
		MsgPtr recv();
		void flush();
		void send(MsgPtr elem);
	};

	 /**
	  * Allow a Python thread to sleep on the incoming queue.
	  */
	class QToPy : public LockedQ {
	public:
		QToPy() {}
		~QToPy() = default;

	private:
		std::condition_variable trigger;
		uint32_t gen = 0;
		void notify();

	public:
		uint32_t wait(uint32_t gen);
		void send(MsgPtr elem);
	};

	 /**
	  * Nothing special (for now)
	  */
	class QToTTD : public LockedQ {
	public:
		QToTTD() {}
		~QToTTD() = default;
	};
}

#endif
