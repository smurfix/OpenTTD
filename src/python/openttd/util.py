#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the+ GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without+ even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the+ GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Some utility functions
"""
from __future__ import annotations

class _add_new_checker(type):
    def __instancecheck__(cls,obj):
        return type(obj) in (cls,cls._DERIV__Base)
    def __call__(cls,*a,**kw):
        return cls._DERIV__Base(*a,**kw)
    def __repr__(self):
        return repr(self._DERIV__Base)
    def __str__(self):
        return str(self._DERIV__Base)
    def __getattr__(self, k):
        return self._DERIV__Base.__getattr__(k)

def extension_of(base):
    """
    Mostly-transparently extend a class or enum with additional methods.
    This is a shorthand for monkeypatching the base class.

    Usage::

        class Base(enums.Enum):
            A=1
            B=2
            C=3

        @for_enum(Base)
        class Deriv:
            def hello(self,x):
                assert isinstance(self,Base)
                return x+self.value

        x1 = Deriv(2)
        x2 = Deriv(x1)
        x3 = Base(2)
        assert x1 is x2
        assert x1 is x3
        assert x3.hello(42) == 44
    """
    def mangler(deriv):
        import _ttd
        import os
        if "PY_OTTD_STUB_GEN" in os.environ:
            return deriv
        for k in dir(deriv):
            if k.startswith("__") and hasattr(base,k):
                continue
            v = getattr(deriv,k)
            setattr(base,k,v)
        for k in ("__members__",):
            try:
                v = getattr(base,k)
            except AttributeError:
                pass
            else:
                try:
                    setattr(deriv,k,v)
                except AttributeError:
                    pass
#                   for kk,vv in v.items():
#                       deriv.__members__[k] = v


        class DERIV(deriv,metaclass=_add_new_checker):
            __Base=base
        DERIV.__name__=deriv.__name__
        return DERIV
    return mangler

async def maybe_async(fn, *a, **kw):
    res = fn(*a, **kw)
    if hasattr(res, "__await__"):
        res = await res
        return res
