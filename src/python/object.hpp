/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef PY_OBJECT_H
#define PY_OBJECT_H

#include <nanobind/nanobind.h>
#include <nanobind/stl/unique_ptr.h>
#include <nanobind/stl/shared_ptr.h>

namespace PyTTD { void init_ttd_object(nanobind::module_ &); }

#include "script/script_instance.hpp"
#include "script/script_storage.hpp"
#include "script/api/script_company.hpp"
#include "video/video_driver.hpp"
#include "network/network_internal.h"

#include "python/queues.hpp"

namespace PyTTD {
	namespace py = nanobind;

	class Storage;
	class LockGame;
	typedef std::shared_ptr<Storage> StoragePtr;

	typedef std::unique_ptr<CommandPacket, py::deleter<CommandPacket>> CommandPacketPtr;

	/*
	 * Python-compatible Storage objects are managed via a shared pointer.
	 */
	class NB_IMPORT Storage : public ScriptStorage, std::enable_shared_from_this<Storage> {
		struct Private { explicit Private() = default; };

		friend void PyTTD::init_ttd_object(nanobind::module_&);
		friend LockGame;
	public:
		// This constructor, despite (necessarily) being public,
		// is only usable by class methods.
		Storage(Private) : ScriptStorage() { }

		// Thus all objects must be contained in a shared_ptr.
		static StoragePtr Create(ScriptCompany::CompanyID comp)
		{
			auto res = std::make_shared<Storage>(Private());
			res->root_company = (Owner)comp;
			res->company = (Owner)comp;
			return res;
		}

		virtual ~Storage() = default;

		static StoragePtr from_python();
		py::object get_result();
		void add_result(py::object obj);

	private:
		py::object cmd_result = py::none();
	};
}

#endif /* PY_OBJECT_H */
