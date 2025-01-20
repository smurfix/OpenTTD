#!/usr/bin/env python3

import sys
import re
from pathlib import Path

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <sourcefile>", file=sys.stderr)
    sys.exit(1)
(_, SCRIPT_API_FILE) = sys.argv

api_file = Path(SCRIPT_API_FILE)

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
enum_member_re = re.compile(r'^\s*(\S+),')
enum_err_re = re.compile(r'^\[(.*)\]')
end_re = re.compile(r'^\s*};')
method_re = re.compile(r'^\s*((virtual|static|const)\s+)*(\S+\s+[&*]?)?(~?\S+)\s*\(((::|[^:])*)\)')

public_re = re.compile(r'^\s*public')
private_re = re.compile(r'^\s*private')
protected_re = re.compile(r'^\s*protected')

upcase_re = re.compile("[A-Z0-9]+")

def strip_var(p: str) -> str:
    """removes the last word
    """
    p = p.rstrip()
    try:
        p,x = p.rsplit(" ", 1)
    except ValueError:
        pass
    else:
        if x[0] in ("&","*"):
            p += " "+x[0]
    return p

def to_snake(s: str) -> str:
    """Converts a camel case or pascal case string to snake case.

    Args:
        camel_string:
            String in camel case or pascal case format. For example myVariable.

    Returns:
        The string in snake case format. For example my_variable.
    """

    return upcase_re.sub(lambda x: "_"+x.group(0).lower(), s).lstrip("_")

def reset_reader():
    global cls_name
    global enum_name
    global cls_level
    cls_name=None
    api_cls=None
    enum_name=None
    cls_level=0

def doxygen_check():
    if doxygen_skip is not None:
        raise SyntaxError(f"{api_file}:{num_line}: a DOXYGEN_API block was not properly closed")

print(f"""
#include "script/api/{api_file.name}"

namespace PyTTD {{
""")


for num_line,line in enumerate(api_file.read_text().split("\n")):
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
        elif f"-python" in line:
            api_selected = False
        elif f"python" in line or "game" in line:
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
                    print(f"/* TODO: {cls_super}::{cls_name} refers to the Squirrel VM */")
                    cls_super = None
                    cls_name = None
                    pass
                else:
                    api_selected = None
                    api_cls = cls_name
                    if api_cls.startswith("Script"):
                        api_cls = api_cls[6:]
                    print(f'void init_{api_cls.lower()}(py::module_ &m)')
                    print('{');
                    print(f'    auto cls_{cls_name} = py::class_<{cls_name}, {cls_super}>(m, "{api_cls}");')

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

        # Check if we want to publish this struct
        if api_selected is None:
            api_selected = cls_in_api
        if not api_selected:
            api_selected = None
            continue
        api_selected = None

        if not is_public or cls_level != 1:
            continue

        cls_name = m.group(1)
        continue

    # We need to make specialized conversions for enums
    if m := enum_re.match(line):
        cls_level += 1

        # Check if we want to publish this enum
        if not api_selected:
            api_selected = cls_in_api
        if not api_selected:
            api_selected = None
            continue
        api_selected = None

        if not is_public or api_cls is None:
            continue

        enum_cls = cls_name
        enum_name = m.group(1)
        ename = enum_name
        if ename.startswith(api_cls):
            ename = ename[len(api_cls):]
        if ename == "":
            # Umm, no.
            enum_cls=enum_name=None
            continue
        if enum_name == "ErrorMessages":
            print(f'    auto enum_{enum_cls} = py::enum_<{enum_cls}::{enum_name}>(m, "_Error_{enum_cls}")')
        else:
            print(f'    py::enum_<{enum_cls}::{enum_name}>(m, "{ename}")')
        continue

    # Maybe the end of the class
    if end_re.match(line):
        cls_level -= 1
        if cls_level:
            if enum_name is not None:
                # print(f'        .export_values()')
                print(f'        ;\n')
                if enum_name == "ErrorMessages":
                    print(f'    m.attr("Error") = enum_{enum_cls};')

                enum_name = None
                continue
        if cls_name and not cls_level:
            print("}")
            cls_name = None
            api_cls = None

    # Skip non-public functions
    if not is_public:
        continue

    # Add enums
    if enum_name is not None and (m := enum_member_re.match(line)):
        name = m.group(1)

        # Chop prefixes off enum constants.
        pname = name
        if enum_name == "ErrorMessages":
            if pname.startswith("ERR_"):
                pname = pname[4:]
        if api_cls and pname.startswith(api_cls.upper()+"_"):
            # ERR_VEHICLE_TOO_MANY ⇒ vehicle.Error.TOO_MANY
            pname = pname[len(api_cls)+1:]
        else:
            # vehicle.VehicleType::VT_RAIL ⇒ vehicle.Type.RAIL
            upn = ''.join(x for x in enum_name if x.isupper())+"_"
            if pname.startswith(upn):
                pname = pname[len(upn):]

        print(f'        .value("{pname}", {enum_cls}::{name})')

        # Check if this a special error enum
        if enum_name == "ErrorMessages":
            # syntax:
            # enum ErrorMessages {
            #	ERR_SOME_ERROR,	// [STR_ITEM1, STR_ITEM2, ...]
            # }

            # Set the mappings
            if em := enum_err_re.search(line):
                for err_str in em.group(1).split(","):
                    err_str = err.strip()
                    enum_err2str.setdefault(name,[]).append(err_str)
                    enum_str2err[err_str] = name
        continue

    # a const (non-enum) value
    if m := const_re.match(line):
        name = m.group(1)
        if cls_name is not None:
            print(f'''\
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wignored-qualifiers"
    m.attr("{name}") = (decltype({cls_name}::{name})) {cls_name}::{name};
#pragma GCC diagnostic pop
''')
        continue

    # Add a method to the list
    if m := method_re.match(line):
        if want_skip:
            skip_next = True
            continue
        if cls_level != 1:
            continue
        meta = m.group(1)
        typ = m.group(3)
        name = m.group(4)
        params = m.group(5)
        if line.rstrip().endswith(":"):
            skip_next = True

        params = ",".join(strip_var(p) for p in params.split(","))

        if name.startswith("~"):
            if api_selected:
                print(f"Destructor for '{cls_name}' has @api. Tag ignored.", file=sys.stderr)
                api_selected = None
            continue

        is_static = meta is not None and "static" in meta

        if name == cls_name:
            if api_selected:
                print(f"Constructor for '{cls_name}' has @api. Tag ignored.", file=sys.stderr)
                api_selected = None

            if cls_super == "ScriptEvent":
                pass
            elif "HSQUIRRELVM" in params:
                print(f'    /* TODO init {cls_name}.def(py::init<{params}>()); */');
            else:
                print(f'    cls_{cls_name}.def(py::init<{params}>());');
            continue

        if api_selected is None:
            api_selected = cls_in_api
        if not api_selected:
            api_selected = None
            continue
        api_selected = None

        if name.startswith("_"):
            continue

        if cls_name:  # yes, even if static
            if "HSQUIRRELVM" in params:
                print(f"/* TODO: {cls_name}::{name} refers to the Squirrel VM */")
                continue

            if is_static:
                print(f'    m.def("{to_snake(name)}", wrap {{ {cls_name}::{name} }});')
            else:
                print(f'    cls_{cls_name}.def("{to_snake(name)}", wrap<decltype(&{cls_name}::{name})> {{& {cls_name}::{name} }});')

print("\n} /* EOF */")

doxygen_check()

