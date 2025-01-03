/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/queues.hpp"

#include <memory>

using namespace PyTTD;

namespace PyTTD {
	void QToPy::notify() {
		{
			std::unique_lock lk(lock);
			if(++gen > 9999)
				gen = 1;
		}
		trigger.notify_one();
	}

	void LockedQ::send(MsgPtr elem) {
		std::unique_lock lk(lock);
		queue.push(std::move(elem));
	}

	void QToPy::send(MsgPtr elem) {
		LockedQ::send(std::move(elem));
		notify();
	}

	MsgPtr LockedQ::recv() {
		std::unique_lock lk(lock);

		if (queue.size() == 0)
			return {};
		MsgPtr res = std::move(queue.front());
		queue.pop();
		return res;
	}

	uint32_t QToPy::wait(uint32_t gen) {
		std::unique_lock lk(lock);
		if (gen == this->gen) {
			trigger.wait(lk);
		}
		return this->gen;
	}
}

