#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This code creates a facsimile of the _ttd module so automated tests that
run outside of OpenTTD have a remote chance of working.

Usage:
    openttd -Y "dump_ttd.py openttd/_stub/data.py"
"""
from __future__ import annotations

from types import ModuleType
from inspect import signature
from openttd._util import _Sub
import enum
import re
from nanobind.stubgen import StubGen

def_re = re.compile(r"def \w+(\(.*\)( ->.*)?):")

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any

_block = {
    "_ttd_msg__Msg",
    "_ttd_object_SimpleCountedObject",
    "_ttd_object_ScriptObject",
    "_ttd_script_list_List",
    "_ttd_script_tilelist_TileList",
}
class _attr:
    def __init__(self, d):
        self.__d = d
    def __getattr__(self,k):
        try:
            return self.__d[k]
        except KeyError:
            raise AttributeError(k) from None
    def __iter__(self):
        return iter(self.__d)

def expo(prefix:str, name:str, mod: Any, fw):
    mods = {}
    vals = {}
    clas = {}
    prcs = {}

    prefix = f"{prefix}{'.' if prefix else '_'}{name}"
    pre_fix = prefix.replace('.','_')


    if isinstance(mod,enum.EnumType):
        for t in (enum.IntFlag,enum.IntEnum,enum.Flag,enum.Enum):
            if issubclass(mod,t):
                etyp=f"enum.{t.__name__}"
                break
        print(f"class {pre_fix}({etyp}):", file=fw)
        for t in mod:
            print(f"    {'_' if t.name[0].isdigit() else ''}{t.name} = {t.value !r}", file=fw)

        for t in mod:
            if t.name[0].isdigit():
                print(f"{pre_fix}.__members__[{t.name !r}] = {pre_fix}._{t.name}", file=fw)
        print("", file=fw)
        return

    for k in _attr(mod.__dict__) if isinstance(mod,(type,_Sub,int)) else dir(mod):
        if k.startswith("__"):
            if not isinstance(mod,type):
                continue
            if k.endswith("__") and k[2:-2] in {"module","dict","weakref","doc","class"}:
                continue
        v = getattr(mod,k)
        if isinstance(v,ModuleType):
            mods[k]=v
        elif isinstance(v,type):
            clas[k]=v
        elif callable(v):
            prcs[k]=v
        else:
            vals[k]=v

    for k,v in mods.items():
        expo(prefix, k, v, fw)
    for k,v in clas.items():
        if f"{pre_fix}_{k}" in _block:
            continue
        sg = StubGen(mod)
        sg.put(v)
        print("# STUB #", file=fw)
        stub = sg.get()
        stub = stub.replace("class ",f"class {pre_fix}_",1)
        stub = stub.replace("_ttd.object.","")
        stub = stub.replace("_ttd.script.list.List","List")
        stub = stub.replace("\n\n","\n")
        stub = stub.replace("import enum\n","")
        stub = stub.replace("import _ttd\n","")
        stub = stub.replace("from typing import overload\n","")
        print(stub.lstrip("\n"),file=fw)
        if k != "Error":
            print(f"{k} = {pre_fix}_{k}",file=fw)
        # expo(prefix, k, v, fw)
        #print(f"{pre_fix}_{k} = {k}; del {k}\n", file=fw)

    if clas:
        print("")
    for k in clas.keys():
        if k == "Error" or f"{pre_fix}_{k}" in _block:
            continue
        print(f"del {k}",file=fw)
    if clas:
        print("")


    if isinstance(mod,(_Sub,ModuleType)):
        print(f"class {pre_fix}(_Sub):", file=fw)
    else:
        print(f"class {pre_fix}:", file=fw)

    if d := getattr(mod,"__doc__",None):
        print(f"    {repr(d)}", file=fw)
    for k in mods.keys():
        if f"{pre_fix}_{k}" in _block:
            continue
        print(f"    {k} = {pre_fix}_{k}", file=fw)
    for k in clas.keys():
        if k == "Error":
            continue
        if f"{pre_fix}_{k}" in _block:
            continue
        print(f"    {k} = {pre_fix}_{k}", file=fw)
    for k,v in vals.items():
        v = repr(v)
        if v[0] == "<":
            print(f"    {k} = Unknown('{prefix}.{k}', {v !r})", file=fw)
        else:
            print(f"    {k} = {v !r}", file=fw)
    for k,v in prcs.items():
        try:
            sg = StubGen(mod)
            sg.put(v)
            if (r := def_re.search(sg.get())):
                sig = r.group(1)
            else:
                sig = "(*a,**kw) -> Any"
        except ValueError:
            sig = str(signature(v))
        print(f"    def {k}{sig}:", file=fw)
        d = getattr(v,"__doc__",None) or ""
        d = d.replace(f"{k}{sig}","")
        if d:
            print(f"        {repr(d)}", file=fw)
        print(f"        ...", file=fw)

    if not mods and not clas and not vals and not prcs:
        print(f"    pass  # empty", file=fw)
    print("", file=fw)



def run(main, *a):
    import _ttd
    import sys
    if len(a) > 1:
        raise ValueError("One optional argument: the output filename")

    from pathlib import Path
    if len(a) == 1:
        f=Path(a[0])
    else:
        import openttd as _ottd
        f=Path(_ottd.__file__).parent/"_stub"/"data.py"

    with open(f,"w",encoding="utf-8") as fw:
        print("""\
#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

# THIS FILE IS AUTO-GENERATED; PLEASE DO NOT ALTER MANUALLY

'''
This is an auto-generated stub module that mimics the '_ttd' module.

The '_ttd' module represents the C++ code in OpenTTD that interfaces it to
Python. We don't want to start OpenTTD for running Python-only tests.

Hence this code.
'''
from __future__ import annotations

import enum
from typing import overload
from openttd._util import _Sub, Unknown

class _ttd_msg__Msg:
    pass
_Msg=_ttd_msg__Msg

class _ttd_object_SimpleCountedObject:
    pass
SimpleCountedObject=_ttd_object_SimpleCountedObject

class _ttd_object_ScriptObject:
    pass
ScriptObject=_ttd_object_ScriptObject

class List:
    pass

class TileList(List):
    pass

class _Text:
    pass
""", file=fw)

        expo("","ttd",_ttd,fw)  # the '_' prefix is auto-added by 'expo'
        print("""\
_ttd.msg._Msg = _Msg; del _Msg
_ttd.object.SimpleCountedObject = SimpleCountedObject; del SimpleCountedObject
_ttd.object.ScriptObject = ScriptObject; del ScriptObject
_ttd.ttd_script_list_List = List; del List
_ttd_script_tilelist_TileList = TileList; del TileList
""", file=fw)
    print(f"Export to {str(f) !r} finished.")
