#!/usr/bin/env python3

import sys
import re
from pathlib import Path

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} <sourcefile> <destfile> <name/prefix…,…>", file=sys.stderr)
    sys.exit(1)
(_, source_file,dest_file,enum_names) = sys.argv

source_file = Path(source_file)
dest_file = Path(dest_file)
file_name = source_file.stem
dest = dest_file.open("w")

names = {}
for name in enum_names.split(","):
    mode = []
    name,*prefix = name.split("/")
    if name[0] == "*":
        name = name[1:]
        mode.append(',py::is_flag(),py::is_arithmetic()')

    names[name] = (mode,*prefix)


enum_name=None
cls_name=None
api_cls=None
cls_super=None
cls_param=""
cls_in_api=False
cls_level=0
api_selected=None
is_public=None

doxygen_skip=None
squirrel_skip=None
skip_next=False

const_re = re.compile(r'^\s*static const \S+ (\S+) = (\S+)?\s*;')
api_re = re.compile(r'^\s*\* @api (.*)$')
fwd_re = re.compile(r'^\s*class(.*);')
cls_re = re.compile(r'\s*class (.*) (: public|: protected|: private|:) (\S+)')
struct_re = re.compile(r'^\s*struct (\S*)')
enum_re = re.compile(r'^\s*enum (\S*)')
enum_member_re = re.compile(r'^\s*([a-zA-Z][a-zA-Z0-9_]*)(,|\s*=|\s*$)')
enum_err_re = re.compile(r'^\[(.*)\]')
end_re = re.compile(r'^\s*};')
method_re = re.compile(r'^\s*((virtual|static|const)\s+)*(\S+\s+[&*]?)?(~?\S+)\s*\(((::|[^:])*)\)')

public_re = re.compile(r'^\s*public')
private_re = re.compile(r'^\s*private')
protected_re = re.compile(r'^\s*protected')

upcase_re = re.compile("[A-Z0-9]+")

def doxygen_check():
    if doxygen_skip is not None:
        raise SyntaxError(f"{api_file}:{num_line}: a DOXYGEN_API block was not properly closed")

dest.write(f"""

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

namespace py = nanobind;

#include "{source_file.name}"

namespace PyTTD {{

void init_ttd_enum_{file_name}(py::module_ &m) {{

""")


for num_line,line in enumerate(source_file.read_text().split("\n")):
    num_line += 1
    want_skip,skip_next = skip_next,False

    # lightly check Doxygen ifdefs
    if line.startswith("#ifndef DOXYGEN_API"):
        doxygen_check()
        doxygen_skip=False
        continue
    if line.startswith("#ifdef DOXYGEN_API"):
        doxygen_check()
        doxygen_skip=True
        continue
    if line.startswith("#endif /* DOXYGEN_API */"):
        doxygen_skip=None
        continue
    if line.startswith("#else"):
        if isinstance(doxygen_skip, bool):
            doxygen_skip = not doxygen_skip
        continue
    if doxygen_skip:
        continue

    if m := api_re.match(line):
        line = m.group(1)
        # By default, classes are not selected
        if cls_level == 0:
            api_selected = False

        if line in ("none","-all"):
            api_selected = False
        elif f"-{api_lc}" in line:
            api_selected = False
        elif f"{api_uc}" == "Template":
            api_selected = True
        elif f"{api_lc}" in line or "game" in line:
            api_selected = True
        continue

    # Remove the old squirrel stuff
    if line.startswith("#ifdef DEFINE_SQUIRREL_CLASS"):
        squirrel_skip=True
        continue
    if line.startswith("#endif /* DEFINE_SQUIRREL_CLASS */"):
        squirrel_skip=False
        continue
    if squirrel_skip:
        continue

    # Ignore forward declarations of classes
    if fwd_re.match(line):
        continue

    # We only want to have public functions exported for now
    if m := cls_re.match(line):
        if cls_level == 0:
            if api_selected is None:
                print(f"Class '{m.group(1)}' has no @api. It won't be published to any API.", file=sys.stderr)
                api_selected = False
            is_public=None
            cls_in_api = api_selected
            if cls_in_api:
                cls_name=m.group(1)
                cls_super=m.group(3)
                if cls_name in ("ScriptPriorityQueue",):
                    dest.write(f"/* TODO: {cls_super}::{cls_name} refers to the Squirrel VM */\n")
                    cls_super = None
                    cls_name = None
                    pass
                else:
                    api_selected = None
                    api_cls = cls_name
                    if api_cls.startswith("Script"):
                        api_cls = api_cls[6:]
                    dest.write(f'''
void init_{api_cls.lower()}(py::module_ &m) {{
    auto cls_{cls_name} = py::class_<{cls_name}, {cls_super}>(m, "{api_cls}");
''')
        elif cls_level == 1:
            # TODO export structs
            print(f"Struct {m.group(1)}: TODO",file=sys.stderr)
            api_selected = None

        cls_level += 1
        continue

    if public_re.match(line):
        if cls_level == 1:
            is_public = True
        continue
    if protected_re.match(line):
        if cls_level == 1:
            is_public = False
        continue
    if private_re.match(line):
        if cls_level == 1:
            is_public = False
        continue

    if "*/" in line:
        comment = False
        continue
    if "/*" in line:
        comment = True
        continue
    if comment:
        continue

    # We need to make specialized conversions for structs
    if m := struct_re.match(line):
        cls_level += 1
        continue

    # We need to make specialized conversions for enums
    if m := enum_re.match(line):
        cls_level += 1

        try:
            modes,*prefix = names[m.group(1)]
        except KeyError:
            continue

        enum_name = m.group(1)
        ename = enum_name
        if ename[-1] == "s":
            ename = ename[:-1]  # strip plural
        dest.write(f'    py::enum_<{enum_name}>(m, "{ename}" {''.join(modes)})\n')
        continue

    # Maybe the end of the class
    if end_re.match(line):
        cls_level -= 1
        if enum_name is not None:
            # dest.write(f'        .export_values()')
            dest.write(f'        ;\n')
            enum_name = None
            continue

    # Add enums
    if enum_name is not None and (m := enum_member_re.match(line)):
        name = m.group(1)

        # Chop prefixes off enum constants.
        pname = name
        for pref in prefix:
            if pname.startswith(pref):
                # ERR_VEHICLE_TOO_MANY ⇒ vehicle.Error.TOO_MANY
                pname = pname[len(pref):]
                break

        dest.write(f'        .value("{pname}", {enum_name}::{name})\n')
        continue

dest.write("}\n} /* EOF */")
dest.close();

doxygen_check()

