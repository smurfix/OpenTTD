/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#include <nanobind/nanobind.h>
#include <nanobind/stl/shared_ptr.h>

#include <iostream>
#include <memory>

#include "python/wrap.hpp"

#include "script/api/script_object.hpp"
#include "script/script_storage.hpp"

namespace PyTTD {
	Wrapper::Wrapper() : drv(reinterpret_cast<VDriver *>(VDriver::GetInstance())) {
		if (drv == nullptr) [[unlikely]] {
			throw std::domain_error("No Driver");
		}
		drv->GetStateMutex().lock();
	}

	Wrapper::~Wrapper() {
		drv->GetStateMutex().unlock();
	}
}
