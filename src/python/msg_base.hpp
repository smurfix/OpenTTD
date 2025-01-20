/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_MSG_BASE_H
#define PY_MSG_BASE_H

#include <memory>

#include <nanobind/nanobind.h>
#include <nanobind/stl/unique_ptr.h>

namespace PyTTD {

	/**
	 * Base class for messages from/to Python.
	 */

	class MsgBase {
	public:
		virtual void Process() {};

		MsgBase() = default;
		virtual ~MsgBase() = default;
	};

	typedef std::unique_ptr<MsgBase> MsgPtr;

	template<class T, typename ...Args>
	inline MsgPtr NewMsg(Args ... args)
	{
		return std::make_unique<T>(args ...);
	}

	namespace Msg {
		// Initial message to confirm readiness
		class Start : public MsgBase {
		public:
			Start() = default;
			void Process() override;
		};

		// Message that tells the other side to stop work
		class Stop : public MsgBase {
		public:
			Stop() = default;
			void Process() override;
		};
	}
}

#endif
