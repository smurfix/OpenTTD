/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_MSG_MODE_H
#define PY_MSG_MODE_H

#include "python/msg_base.hpp"
#include "openttd.h"


namespace PyTTD::Msg {
	// Game mode changes
	class ModeChange : public MsgBase {
	public:
		ModeChange(GameMode);

		const GameMode &GetMode() { return mode; }
	private:
		GameMode mode;
	};

	class PauseState : public MsgBase {
	public:
		PauseState(PauseMode);

		const PauseMode &GetState() { return paused; }
	private:
		PauseMode paused;
	};
}

#endif
