/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_MSG_CONSOLE_H
#define PY_MSG_CONSOLE_H

#include "python/msg_base.hpp"

#include <memory>
#include <string>
#include <vector>


namespace PyTTD::Msg {
	// Console commands to Python
	class ConsoleCmd : public MsgBase {
	public:
		ConsoleCmd(int argc, const char* const argv[]);

		const std::vector<std::string> &GetArgs() { return args; }
	private:
		std::vector<std::string> args;
	};

	// Message to show on the OpenTTD console
	class ConsoleMsg : public MsgBase {
	public:
		ConsoleMsg(const std::string &msg);
		void Process() override;

		const std::string &GetText() { return text; }
	private:
		std::string text;
	};
}

#endif
