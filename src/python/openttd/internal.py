#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

from typing import TYPE_CHECKING
if not TYPE_CHECKING:
    raise ImportError("This module is only used for typing stubs!")

from enum import IntEnum as _i, IntFlag as _f

import openttd as _t

class _Obj:
    def __init__(self, **kw):
        for k,v in kw.items():
            setattr(self,k,v)

    def _(self, name):
        def set(obj):
            setattr(self,name,obj)
            return obj
        return _at


_t.company = _Obj()
ID=_company_ID)

class _Owner(_f):
    DEITY=42


class Owner(_Owner):
    pass

@_t.company._("ID")
class _company_id(_Owner):
    pass
_t.company = _Obj(ID=_company_ID)


