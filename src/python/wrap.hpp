/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_WRAP_H
#define PY_WRAP_H

#include <nanobind/nanobind.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/shared_ptr.h>

#include "script/script_instance.hpp"
#include "script/script_storage.hpp"
#include "video/video_driver.hpp"

#include "python/instance.hpp"
#include "python/object.hpp"

class VDriver : public VideoDriver {
    public:
		inline std::mutex &GetStateMutex() { return game_state_mutex; }
};

// workaround for those "protected" subclasses
class SObject : public ScriptObject {
	public:
	class AInstance : public ActiveInstance {
		public:
			AInstance(ScriptInstance *instance) : ActiveInstance(instance) {}
			~AInstance() {};
	};
};

namespace PyTTD {
	/**
	 * This RAII wrapper takes the game lock.
	 */
	class LockGame {
	public:
		LockGame();
		virtual ~LockGame();

		// copy/move/assign is forbidden
		LockGame(LockGame const&) = delete;
		LockGame(LockGame &&) = delete;
		LockGame& operator=(LockGame const&) = delete;

	private:
		VDriver *drv;
	};

	py::object cmd_hook(CommandDataPtr cb);

	void cmd_setup();

	// If OpenTTD queued a command, send it to Python.

#   define _WRAP1                                   \
	CommandDataPtr cmd = nullptr;                   \
	{                                               \
	    auto storage = Storage::from_python();      \
		py::gil_scoped_release unlock;              \
		PyTTD::LockGame lock;                       \
		assert(! instance.currentCmd);              \
		{                                           \
			SObject::AInstance active(&instance);   \
			instance.SetStorage(storage);           \

#   define _WRAP2                                   \
		}                                           \
		cmd = std::move(instance.currentCmd);       \
		instance.SetStorage(nullptr);               \
    }                                               \
	if (cmd) {                                      \
		return cmd_hook(std::move(cmd));            \
	}                                               \

	/**
	 * This is the nanobind wrapper that allows us to call Python.
	 */

	// static, returns a value
	template <typename R, typename... Args>
	struct wrap
	{
		using funct_type = R(*)(Args...);
		funct_type func;
		wrap(funct_type f): func(f) {};
		py::object operator()(Args&&... args) const
		{
			R ret;
			_WRAP1
			ret = func(std::forward<Args>(args)...);
			_WRAP2
			return py::cast<const R>((const R)ret);
		}
	};

	// member function, returns a value
	template <typename R, class T, typename... Args>
	struct wrap<R (T::*)(Args...)>
	{
	private:
		using funct_type = R(T:: *)(Args...);
		funct_type func;
	public:
		wrap(funct_type f): func(f) {};
		py::object operator()(T &self, Args&&... args) const
		{
			R ret;
			_WRAP1
			ret = (self.*func)(std::forward<Args>(args)...);
			_WRAP2
			return py::cast<const R>((const R)ret);
		}
	};

	// static, void
	template <typename... Args>
	struct wrap<void, Args...>
	{
		using funct_type = void(*)(Args...);
		funct_type func;
		wrap(funct_type f): func(f) {};
		py::object operator()(Args&&... args) const
		{
			_WRAP1
			func(std::forward<Args>(args)...);
			_WRAP2
			return py::none();
		}
	};

	// member function, void
	template <class T, typename... Args>
	struct wrap<void (T::*)(Args...)>
	{
	private:
		using funct_type = void(T:: *)(Args...);
		funct_type func;
	public:
		wrap(funct_type f): func(f) {};
		py::object operator()(T &self, Args&&... args) const
		{
			_WRAP1
			(self.*func)(std::forward<Args>(args)...);
			_WRAP2
			return py::none();
		}
	};

}

#endif /* PY_WRAP_H */
