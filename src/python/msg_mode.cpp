/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/msg_mode.hpp"
#include "python/task.hpp"
#include "console_func.h"
#include "console_type.h"
#include "safeguards.h"

namespace PyTTD::Msg {

	ModeChange::ModeChange(GameMode mode) {
		this->mode = mode;
	}

	PauseState::PauseState(PauseMode paused) {
		this->paused = paused;
	}
}
