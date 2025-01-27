/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file python/mode.cpp Implementation of ScriptPyMode. */

#include "stdafx.h"
#include "mode.hpp"
#include "script/script_instance.hpp"
#include "script/script_fatalerror.hpp"
#include <iostream>

#include "nanobind/nanobind.h"

#include "safeguards.h"

namespace py = nanobind;

bool ScriptPyMode::ModeProc()
{
	/* In test mode we only return 'false', telling the DoCommand it
	 *  should stop after testing the command and return with that result. */
	nanobind::gil_scoped_acquire _acquire;
	try {
		nanobind::module_ ttd = nanobind::module_::import_("_ttd");
		py::object est = ttd.attr("estimating").attr("get")();
		bool res = ! py::cast<bool>(est);
		return res;
	}
	catch (const std::exception &ex) {
		std::cerr << typeid(ex).name() << std::endl;
		std::cerr << "  what(): " << ex.what() << std::endl;
		return false;
	}
	return false;
}

ScriptPyMode::ScriptPyMode()
{
	this->last_mode     = this->GetDoCommandMode();
	this->last_instance = this->GetDoCommandModeInstance();
	this->SetDoCommandMode(&ScriptPyMode::ModeProc, this);
}

void ScriptPyMode::FinalRelease()
{
	if (this->GetDoCommandModeInstance() != this) {
		/* Ignore this error. */
		return;
	}
	this->SetDoCommandMode(this->last_mode, this->last_instance);
}

ScriptPyMode::~ScriptPyMode()
{
	this->FinalRelease();
}
