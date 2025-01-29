/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _PY_CALL_PY_H
#define _PY_CALL_PY_H

#include <vector>
#include <string>
#include "company_type.h"
#include "command_type.h"


namespace PyTTD {

	struct Script {
		unsigned int id;
		CompanyID company;
		std::string class_;
		std::string info;

		static std::vector<unsigned int> GetIndices();
		static Script *GetIfValid(unsigned int id);
	};

	void Start(const std::string &main = "");
	void Stop(); // tell Python to stop
	bool IsRunning();

	void ProcessFromPython();
	void ConsoleToPy(int argc, const char * const argv[]);

	/* TODO */
	int StartScript(std::string name, std::string params);
	bool StopScript(unsigned int id);

	bool CheckPending(Commands cmd, const CommandDataBuffer &data);
	CommandCallbackData CcPython;
}

#endif
