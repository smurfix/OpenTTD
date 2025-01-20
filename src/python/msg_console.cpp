/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include "python/msg_console.hpp"
#include "python/task.hpp"
#include "console_func.h"
#include "console_type.h"
#include "safeguards.h"

namespace PyTTD::Msg {

	ConsoleCmd::ConsoleCmd(int argc, const char* const argv[]) {
		while(argc > 0) {
			this->args.push_back(*argv);
			argc--; argv++;
		}
	}

	ConsoleMsg::ConsoleMsg(const std::string &msg) {
		this->text = msg;
	}

	void ConsoleMsg::Process() {
		IConsolePrint(CC_DEFAULT, this->text);
	}
}
