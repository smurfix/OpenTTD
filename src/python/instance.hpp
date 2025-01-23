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
	};
	typedef std::unique_ptr<CommandData, py::deleter<CommandData>> CommandDataPtr;


	class NB_IMPORT Instance : public ScriptInstance {
	public:
		Instance() : ScriptInstance("Python") {}
		virtual ~Instance();

		/**
		* Initialize the script and prepare it for its first run.
		* @param info The GameInfo to start.
		*/
		void Initialize(GameInfo *info);

		int GetSetting(const std::string &name) override;
		ScriptInfo *FindLibrary(const std::string &library, int version) override;
		void LoadDummyScript() override {}

		inline void SetStorage(StoragePtr p) { this->py_storage = p; }

		/**
		 * If a call from Python to TTD generated a command, we store it here.
		 */
		CommandDataPtr currentCmd;

	private:
		void RegisterAPI() override;
		void Died() override;

		Storage *GetStorage() override;

		CommandCallbackData *GetDoCommandCallback() override;
		CommandHookProc *GetDoCommandHook() override;

		StoragePtr py_storage;
	};

	extern class Instance instance;

}

#endif /* PY_INSTANCE_HPP */
