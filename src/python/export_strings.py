#!/usr/bin/env python3

import sys
import re
from pathlib import Path

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <sourcefile> <destfile>", file=sys.stderr)
    sys.exit(1)
(_, source_file,dest_file) = sys.argv

source_file = Path(source_file)
dest_file = Path(dest_file)
dest = dest_file.open("w")

str_re = re.compile(r'\sSTR_([A-Z_0-9]+) = (\S+)?\s*;')


class C(dict):
    def __init__(self):
        self.s=dict()
    def _to(self, k):
        return self.s.setdefault(k.lower(),C())
    def bool(self):
        return len(self) > 0 or any(self.s.values())

c=C()
c.s["abbrev"]=C()
c.s["about"]=C()
c.s["ai"]=C()
c.s["ai"].s["config"]=C()
c.s["ai"].s["list"]=C()
c.s["airport"]=C()
c.s["bridge"]=C()
c.s["build"]=C()
c.s["buy"]=C()
c.s["buy"].s["vehicle"]=C()
c.s["cargo"]=C()
c.s["cargo"].s["rating"]=C()
c.s["colour"]=C()
c.s["colour"].s["secondary"]=C()
c.s["company"]=C()
c.s["company"].s["view"]=C()
c.s["company"].s["infrastructure"]=C()
c.s["company"].s["infrastructure"].s["view"]=C()
c.s["config"]=C()
c.s["config"].s["setting"]=C()
c.s["content"]=C()
c.s["content"].s["detail"]=C()
c.s["currency"]=C()
c.s["day"]=C()
c.s["depot"]=C()
c.s["engine"]=C()
c.s["engine"].s["preview"]=C()
c.s["face"]=C()
c.s["finances"]=C()
c.s["finances"].s["section"]=C()
c.s["format"]=C()
c.s["found"]=C()
c.s["framerate"]=C()
c.s["fund"]=C()
c.s["game"]=C()
c.s["game"].s["options"]=C()
c.s["generation"]=C()
c.s["graph"]=C()
c.s["goal"]=C()
c.s["goal"].s["question"]=C()
c.s["goals"]=C()
c.s["group"]=C()
c.s["group"].s["by"]=C()
c.s["help"]=C()
c.s["highscore"]=C()
c.s["house"]=C()
c.s["industry"]=C()
c.s["industry"].s["directory"]=C()
c.s["industry"].s["name"]=C()
c.s["industry"].s["view"]=C()
c.s["intro"]=C()
c.s["just"]=C()
c.s["lai"]=C()
c.s["lai"].s["bridge"]=C()
c.s["lai"].s["clear"]=C()
c.s["lai"].s["object"]=C()
c.s["lai"].s["rail"]=C()
c.s["lai"].s["road"]=C()
c.s["lai"].s["station"]=C()
c.s["lai"].s["water"]=C()
c.s["lai"].s["tunnel"]=C()
c.s["land"]=C()
c.s["land"].s["area"]=C()
c.s["landscaping"]=C()
c.s["livery"]=C()
c.s["local"]=C()
c.s["local"].s["authority"]=C()
c.s["mapgen"]=C()
c.s["menu"]=C()
c.s["misc"]=C()
c.s["month"]=C()
c.s["music"]=C()
c.s["network"]=C()
c.s["network"].s["chat"]=C()
c.s["network"].s["client"]=C()
c.s["network"].s["client"].s["list"]=C()
c.s["network"].s["connecting"]=C()
c.s["network"].s["error"]=C()
c.s["network"].s["server"]=C()
c.s["network"].s["server"].s["list"]=C()
c.s["network"].s["server"].s["message"]=C()
c.s["network"].s["start"]=C()
c.s["network"].s["start"].s["server"]=C()
c.s["newgrf"]=C()
c.s["newgrf"].s["settings"]=C()
c.s["news"]=C()
c.s["order"]=C()
c.s["order"].s["conditional"]=C()
c.s["orders"]=C()
c.s["performance"]=C()
c.s["picker"]=C()
c.s["playlist"]=C()
c.s["purchase"]=C()
c.s["purchase"].s["info"]=C()
c.s["quantity"]=C()
c.s["rail"]=C()
c.s["rail"].s["toolbar"]=C()
c.s["refit"]=C()
c.s["replace"]=C()
c.s["road"]=C()
c.s["road"].s["toolbar"]=C()
c.s["save"]=C()
c.s["save"].s["preset"]=C()
c.s["saveload"]=C()
c.s["scenedit"]=C()
c.s["scenedit"].s["toolbar"]=C()
c.s["screnshot"]=C()
c.s["se"]=C()
c.s["se"].s["mapgen"]=C()
c.s["settings"]=C()
c.s["smallmap"]=C()
c.s["sort"]=C()
c.s["sort"].s["by"]=C()
c.s["sprite"]=C()
c.s["station"]=C()
c.s["station"].s["build"]=C()
c.s["station"].s["list"]=C()
c.s["station"].s["view"]=C()
c.s["story"]=C()
c.s["story"].s["book"]=C()
c.s["subsidies"]=C()
c.s["sv"]=C()
c.s["terraform"]=C()
c.s["textfile"]=C()
c.s["timetable"]=C()
c.s["trees"]=C()
c.s["toolbar"]=C()
c.s["toolbar"].s["tooltip"]=C()
c.s["tooltip"]=C()
c.s["town"]=C()
c.s["town"].s["building"]=C()
c.s["town"].s["building"].s["name"]=C()
c.s["town"].s["view"]=C()
c.s["units"]=C()
c.s["variety"]=C()
c.s["vehicle"]=C()
c.s["vehicle"].s["detail"]=C()
c.s["vehicle"].s["details"]=C()
c.s["vehicle"].s["list"]=C()
c.s["vehicle"].s["name"]=C()
c.s["vehicle"].s["name"].s["aircraft"]=C()
c.s["vehicle"].s["name"].s["road"]=C()
c.s["vehicle"].s["name"].s["road"].s["vehicle"]=C()
c.s["vehicle"].s["name"].s["ship"]=C()
c.s["vehicle"].s["name"].s["train"]=C()
c.s["vehicle"].s["name"].s["train"].s["engine"]=C()
c.s["vehicle"].s["name"].s["train"].s["engine"].s["rail"]=C()
c.s["vehicle"].s["name"].s["train"].s["engine"].s["maglev"]=C()
c.s["vehicle"].s["name"].s["train"].s["engine"].s["monorail"]=C()
c.s["vehicle"].s["name"].s["train"].s["wagon"]=C()
c.s["vehicle"].s["name"].s["train"].s["wagon"].s["rail"]=C()
c.s["vehicle"].s["name"].s["train"].s["wagon"].s["maglev"]=C()
c.s["vehicle"].s["name"].s["train"].s["wagon"].s["monorail"]=C()
c.s["vehicle"].s["status"]=C()
c.s["vehicle"].s["view"]=C()
c.s["viewport"]=C()
c.s["warning"]=C()
c.s["waterways"]=C()


for num_line,line in enumerate(source_file.read_text().split("\n")):
    if (m := str_re.search(line)) is None:
        continue
    name = m.group(1)
    num = int(m.group(2),0)
    name = name.split("_")
    cc=c
    while len(name) > 1:
        if len(name) > 2 and name[1] in ("ERROR","MENU"):
            name = [name[1],name[0]]+name[2:]
            cc._to(name[0])._to(name[1])
            nl = name[0].lower()
        elif (nl := name[0].lower()) not in cc.s:
            break
        cc = cc.s[nl]
        name = name[1:]

    if cc is c:
        cc = c.s["misc"]

    cc["_".join(name)] = num


assert len(c.s["sort"]) == 0
assert len(c.s["sort"].s) == 1
c.s["sort"]=c.s["sort"].s["by"]
c.s["sort"].s["group"]=c.s["group"].s["by"]
del c.s["group"]

cid=1
dest.write("""

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

namespace PyTTD {

    void init_ttd_string_id(py::module_ &m) {
        m.def("_add_strings", [](py::object cls_c) {
            auto c1 = cls_c();

""")
def emit(cc):
    global cid

    this = cid
    for s,i in cc.items():
        dest.write(f"""\
            c{this}["{s}"] = {i};
""")
    for s,cn in cc.s.items():
        if not cn:
            continue
        cid += 1
        dest.write(f"""
            auto c{cid} = cls_c();
            c{this}.attr("{s}") = c{cid};
""")
        emit(cn)
emit(c)

dest.write("""

            return c1;
        });
    }
} /* EOF */
""")
dest.close();

