/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file script_pymode.hpp Switch the script instance to Test Mode. */

#ifndef SCRIPT_PY_MODE_HPP
#define SCRIPT_PY_MODE_HPP

#include "script_object.hpp"

/**
 * Class to switch current mode to Python Mode.
 * In Python mode, whether commands are executed or not depends on the
 *   value returned by `openttd._main._extimating.get()()`.
 * If True, the commands you execute aren't really executed. The system
 *   only checks if it would be able to execute your requests, and what
 *   the cost would be. This is the default in subthreads.
 * If False, commands are executed. Calls return an Awaitable with the
 *   result, assuming that there was no immediate error.
 */
class ScriptPyMode : public ScriptObject {
private:
	ScriptModeProc *last_mode;   ///< The previous mode we were in.
	ScriptObject *last_instance; ///< The previous instance of the mode.

protected:
	/**
	 * The callback proc for Python mode.
	 */
	static bool ModeProc();

public:
	/**
	 * Creating instance of this class switches the build mode to Testing.
	 * @note When the instance is destroyed, it restores the mode that was
	 *   current when the instance was created!
	 */
	ScriptPyMode();

	/**
	 * Destroying this instance reset the building mode to the mode it was
	 *   in when the instance was created.
	 */
	~ScriptPyMode();

	/**
	 * @api -all
	 */
	void FinalRelease() override;
};

#endif /* SCRIPT_PY_MODE_HPP */
