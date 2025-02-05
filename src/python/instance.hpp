/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file python/instance.hpp The PythonInstance links Python with the scripting engine. */

#ifndef PY_INSTANCE_HPP
#define PY_INSTANCE_HPP

#include <nanobind/nanobind.h>
#include <nanobind/stl/unique_ptr.h>

#include "game/game_info.hpp"
#include "script/script_instance.hpp"
#include "python/object.hpp"

namespace py = nanobind;

namespace PyTTD {
	/** Runtime information to link the Python task to the current state. */
	struct CommandData {
		Commands cmd;
		CommandDataBuffer data;
		Script_SuspendCallbackProc *callback;
	};
	typedef std::unique_ptr<CommandData, py::deleter<CommandData>> CommandDataPtr;

	class LockGame;

	class NB_IMPORT Instance : public ScriptInstance {
		friend LockGame;
	public:
		Instance();
		virtual ~Instance();

		/**
		* Initialize the script and prepare it for its first run.
		* @param info The GameInfo to start.
		*/
		void Initialize(GameInfo *info);

		int GetSetting(const std::string &name) override;
		ScriptInfo *FindLibrary(const std::string &library, int version) override;
		void LoadDummyScript() override {}

		inline void SetStorage(StoragePtr p) {
			this->py_storage = p;
			this->storage = &*p;
		}

		/**
		 * If a call from Python to TTD generated a command, we store it here.
		 */
		CommandDataPtr currentCmd;

		void InsertResult(bool result) override;
        void InsertResult(int result) override;

	private:
		void RegisterAPI() override;
		void Died() override;
		Squirrel *dead_engine;

		CommandCallbackData *GetDoCommandCallback() override;
		CommandDoHookProc *GetDoCommandHook() override;
		CommandDoneHookProc *GetDoneCommandHook() override;

	protected:
		StoragePtr py_storage;

	public:
		inline py::object get_result() { return py_storage->get_result(); }
	};

	extern class Instance instance;

}

#endif /* PY_INSTANCE_HPP */
