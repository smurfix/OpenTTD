#!/usr/bin/python3
#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

import sys

_,outf,*names = sys.argv

out = open(outf,"w")

out.write("""
/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/* THIS FILE IS AUTO-GENERATED; PLEASE DO NOT ALTER MANUALLY */

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>

namespace PyTTD {
    namespace py = nanobind;
""")
for name in names:
    out.write(f"    extern void init_ttd_enum_{name}(py::module_ &);\n")

out.write("""
    void init_ttd_enums(py::module_ &mg) {
        auto m = mg.def_submodule("enum", "Assorted auto-generated enums");
""")

for name in names:
    out.write(f"        init_ttd_enum_{name}(m);\n")

out.write("""
    }
}

""")

out.close()
