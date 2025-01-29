/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_WRAP_H
#define PY_WRAP_H

#include <nanobind/nanobind.h>
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
	class StorageSetter {
	public:
		StorageSetter(Instance &instance, StoragePtr storage) : storage(storage),instance(instance) { instance.SetStorage(storage); }
		~StorageSetter() { instance.SetStorage(nullptr); }
	private:
		StoragePtr storage;
		Instance &instance;
	};

	class LockGame {
	public:
		LockGame(StoragePtr);
		virtual ~LockGame();

		// copy/move/assign is forbidden
		LockGame(LockGame const&) = delete;
		LockGame(LockGame &&) = delete;
		LockGame& operator=(LockGame const&) = delete;

	private:
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

	/**
	 * This is the nanobind wrapper that allows us to call Python.
	 * We need to fetch the storage with the GIL held, and we cannot
	 * release the GIL in a RAII object because re-acquiring it can
	 * throw an exception, so the first two lines of this wrapper
	 * must be open-coded.
	 *
	 * TODO somebody might want to convert this to a template …
	 */

#define _WRAP1                                 \
	CommandDataPtr cmd = nullptr;              \
	{                                          \
		auto storage = Storage::from_python(); \
		auto state = PyEval_SaveThread();      \
		{                                      \
			LockGame lock(storage);            \

#define _WRAP2                                 \
		}                                      \
		cmd = std::move(instance.currentCmd);  \
		PyEval_RestoreThread(state);           \
	}                                          \
	if (cmd) {                                 \
		return cmd_hook(std::move(cmd));       \
	}                                          \

	// Trimmed-down wrapper for object instantiation
	//
#define _WRAP1_NEW                             \
	{                                          \
		auto storage = Storage::from_python(); \
		auto state = PyEval_SaveThread();      \
		{                                      \
			LockGame lock(storage);            \

#define _WRAP2_NEW                             \
		}                                      \
		PyEval_RestoreThread(state);           \
	}                                          \

	// ... and a modified copy of nanobind's "new_" template as a wrap for
	// *that*:
	//
	using namespace nanobind;

	template <typename Func, typename Sig = detail::function_signature_t<Func>>
	struct wrap_new;

	template <typename Func, typename Return, typename... Args>
	struct wrap_new<Func, Return(Args...)> : def_visitor<wrap_new<Func, Return(Args...)>> {
		std::remove_reference_t<Func> func;

		wrap_new(Func &&f) : func((detail::forward_t<Func>) f) {}

		template <typename Class, typename... Extra>
		NB_INLINE void execute(Class &cl, const Extra&... extra) {
			// If this is the first __new__ overload we're defining, then wrap
			// nanobind's built-in __new__ so we overload with it instead of
			// replacing it; this is important for pickle support.
			// We can't do this if the user-provided __new__ takes no
			// arguments, because it would make an ambiguous overload set.
			constexpr size_t num_defaults =
				((std::is_same_v<Extra, arg_v> ||
				std::is_same_v<Extra, arg_locked_v>) + ... + 0);
			constexpr size_t num_varargs =
				((std::is_same_v<detail::intrinsic_t<Args>, args> ||
				std::is_same_v<detail::intrinsic_t<Args>, kwargs>) + ... + 0);
			detail::wrap_base_new(cl, sizeof...(Args) > num_defaults + num_varargs);

			auto wrapper = [func_ = (detail::forward_t<Func>) func](handle, Args... args) {
				Return result;
				_WRAP1_NEW
				result = func_((detail::forward_t<Args>) args...);
				_WRAP2_NEW
				return result;
			};

			auto policy = call_policy<detail::new_returntype_fixup_policy>();
			if constexpr ((std::is_base_of_v<arg, Extra> || ...)) {
				// If any argument annotations are specified, add another for the
				// extra class argument that we don't forward to Func, so visible
				// arg() annotations stay aligned with visible function arguments.
				cl.def_static("__new__", std::move(wrapper), arg("cls"), extra...,
							policy);
			} else {
				cl.def_static("__new__", std::move(wrapper), extra..., policy);
			}
			cl.def("__init__", [](handle, Args...) {}, extra...);
		}
	};
	template <typename Func> wrap_new(Func&& f) -> wrap_new<Func>;

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
