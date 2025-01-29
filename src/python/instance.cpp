/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file python/instance.cpp Implementation of Python "script" Instance. */

#include "instance.hpp"

#include "error.h"

#include "script/squirrel_class.hpp"
#include "script/script_storage.hpp"
#include "script/script_cmd.h"
#include "script/script_gui.h"

#include "game/game_text.hpp"

#include "python/task.hpp"
#include "python/msg_command.hpp"

#include "stdafx.h"
#include "safeguards.h"

namespace py = nanobind;

namespace PyTTD {

	Instance::Instance() : ScriptInstance("Python")
	{
		dead_engine = nullptr;
	}

	// GIL must be held
	void Instance::InsertResult(bool result)
	{
		py_storage->add_result(py::bool_(result));
	}

	// GIL must be held
	void Instance::InsertResult(int result)
	{
		py_storage->add_result(py::int_(result));
	}

	void Instance::Initialize(GameInfo *info)
	{
		this->versionAPI = info->GetAPIVersion();

		/* Register the GameController */
		// SQGSController_Register(this->engine);

		delete this->engine;
		this->engine = nullptr;

		ScriptInstance::Initialize(info->GetMainScript(), info->GetInstanceName(), OWNER_DEITY);
	}

	void Instance::RegisterAPI()
	{
		ScriptInstance::RegisterAPI();

		/* Register all classes */
		// SQGS_RegisterAll(this->engine);

		RegisterGameTranslation(this->engine);

		if (!this->LoadCompatibilityScripts(this->versionAPI, GAME_DIR)) this->Died();
	}

	int Instance::GetSetting(const std::string &name)
	{
		(void)name;
		return 0;
	}

	ScriptInfo *Instance::FindLibrary(const std::string &library, int version)
	{
		(void)library;
		(void)version;
		return nullptr;
	}

	void Instance::Died()
	{
		ScriptInstance::Died();

		/* Don't show errors while loading savegame. They will be shown at end of loading anyway. */
	}

	/**
	 * "CommandCallback" function for commands executed by Python scripts.
	 * @param cmd command as given to DoCommandPInternal.
	 * @param result The result of the command.
	 * @param data Command data as given to Command<>::Post.
	 * @param result_data Additional returned data from the command.
	 */
	void CcPython(Commands cmd, const CommandCost &result, const CommandDataBuffer &data, CommandDataBuffer result_data)
	{
		if (! Task::IsRunning())
			return;
		Task::Send(NewMsg<Msg::CmdResult>(cmd, result, data, result_data));
	}

	CommandCallbackData *Instance::GetDoCommandCallback()
	{
		return &CcPython;
	}

	static void saveCmd(Commands cmd, CommandDataBuffer data, Script_SuspendCallbackProc *callback) {
		if(instance.currentCmd)
			throw std::domain_error("Second command");
		instance.currentCmd.reset(new CommandData());
		instance.currentCmd->cmd = cmd;
		instance.currentCmd->data = data;
		instance.currentCmd->callback = callback;
	}

	static void sendResult(Commands cmd, const CommandCost &result, TileIndex tile)
	{
		// XXX this happens to work without taking the GIL, but beware
		py::object data = instance.get_result();
		Task::Send(NewMsg<Msg::CmdResult3>(cmd, result, tile, _current_company, data));
	}

	CommandDoHookProc *Instance::GetDoCommandHook() {
		return &saveCmd;
	}
	CommandDoneHookProc *Instance::GetDoneCommandHook() {
		return &sendResult;
	}

	// The empty destructor is there to tell the compiler to create the class
	Instance::~Instance() { }

	// This is our singleton script instance.
	// We activate it during calls from Python.
	Instance instance;
}
