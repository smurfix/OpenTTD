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
#include "framerate_type.h"
#include "core/backup_type.hpp"

#include "python/instance.hpp"
#include "python/object.hpp"
#include "python/mode.hpp"

// workarounds for "protected" objects in the core game.
// TODO: add appropriate "friend" declarations instead.
//
class SObject : public ScriptObject {
	public:
	class AInstance : public ActiveInstance {
		public:
			AInstance(ScriptInstance *instance) : ActiveInstance(instance) {}
			~AInstance() {};
	};
	inline static void SetDoCommandMode(ScriptModeProc *proc, ScriptObject *instance) {
		ScriptObject::SetDoCommandMode(proc, instance);
	}
};

class VDriver : public VideoDriver {
	public:
		inline std::mutex &GetStateMutex() { return game_state_mutex; }
};

namespace PyTTD {

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wattributes"
	/**
	 * This RAII wrapper takes the game lock and sets everything up for
	 * interfacing with Python.
	 *
	 * It can of course be simplified for API calls that don't read
	 * complex data structures or don't send commands.
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
		class StorageSetter {
		public:
			StorageSetter(Instance &instance, StoragePtr storage) : storage(storage),instance(instance) { instance.SetStorage(storage); }
			~StorageSetter() { instance.SetStorage(nullptr); }
		private:
			StoragePtr storage;
			Instance &instance;
		};

		// The code setting this up is in 'wrap.cpp'.
		//
		// Python holds a Storage object. Fetch that.
		StoragePtr storage;

		// Release the GIL.
		py::gil_scoped_release unlock;

		// Pointer to the Driver, necessary for accessing the game lock.
		VDriver *drv;

		// Holds the game lock.
		std::lock_guard<std::mutex> lock;

		// Now that we have the lock, we affect performance, so measure.
		PerformanceMeasurer framerate;

		// Adapter to set the active script instance to Python's.
		SObject::AInstance active;

		// Adapter to set the instance's storage.
		StorageSetter storage_set;

		// Get the script mode (exec/test) from the current Python context.
		ScriptPyMode mode;

		// Set (and restore) the current company
		Backup<CompanyID> cur_company;
		// ... and now we can safely access the script API; after that, the
		// object destructors undo everything in the correct order.
		//
		// If the script generated a command, the command hook in our
		// instance will store that in 'instance.currentCmd'. When we're
		// back in Python context, our 'cmd_hook' function queues it for
		// processing by the "real" game loop.
	};

	py::object cmd_hook(CommandDataPtr cb);

	void cmd_setup();

#define _WRAP1                                 \
	CommandDataPtr cmd = nullptr;              \
	{                                          \
		LockGame lock;                         \

#define _WRAP2                                 \
		cmd = std::move(instance.currentCmd);  \
	}                                          \
	if (cmd) {                                 \
		return cmd_hook(std::move(cmd));       \
	}                                          \

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
#pragma GCC diagnostic pop

}

#endif /* PY_WRAP_H */
