#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the+ GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without+ even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the+ GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#
"""
Errors
"""
from __future__ import annotations

import _ttd
import re
ctrl_re=re.compile("[\ue000-\ue0ff]+")

class TTDError(RuntimeError):
    """
    This is a generic error you can use to catch errors from the OpenTTD
    integration (as opposed to the rest of the Python system).

    It is never raised directly; only subclasses are.
    """
    pass

class TTDExecError(TTDError):
    """
    This error is raised when a command to OpenTTD failed.
    @err: error number.
    @error: the enum member that corresponds to @err.

    Call `resolve` to fill @error.

    It is never raised directly; only subclasses are.
    """
    error = None

    def __init__(self, err=None):
        if err is None:
            raise RuntimeError("No Error!")
        if isinstance(err,str):
            self.error = err
            self.err = -1
        else:
            self.err = err

    def resolve(self):
        """
        Resolve error number
        """
        # get the error enum
        if self.error is not None:
            return
        try:
            err = _ttd.script.error.Error(self.err).name
        except ValueError:
            for tag in ("bridge","marine","order","rail","road","sign"):
                try:
                    err = getattr(_ttd.script,tag).Error(self.err).name
                except (AttributeError,ValueError):
                    pass
                else:
                    break
            else:
                err = "?"
        self.error = err

    def __repr__(self):
        if self.err == -1:
            return f"{self.error}"
        return f"{self.err}"

    def __str__(self):
        return f"{self.err}:{self.error}"

class TTDCommandError(TTDExecError):
    """
    This error is raised when a command to OpenTTD failed;
    it encapsulates the command and its arguments.
    @name: a human-readable name of the command.

    Call `resolve` to fill @name.

    Don't catch this exception; catch `TTDExecError` instead.
    """
    name = None

    def __init__(self,proc,a,kw, result=None, err=None):
        self.proc = proc
        self.a = a
        self.kw = kw
        self.result = result
        if result is not None:
            assert err is None
            err = result.message
            if result.extra_message is not None:
                err += " "+result.extra_message
            err=ctrl_re.sub("",err)
        super().__init__(err)

    def resolve(self):
        """
        Resolve name and error number
        """
        if self.name is not None:
            return
        super().resolve()

        # get the qualified method name
        proc = self.proc
        try:
            name = proc.__nb_signature__[0][0]
        except AttributeError:
            name = proc.__name__
        else:
            if name.startswith("def "):
                name = name[4:]
            if (i := name.find("(")) > 0:
                name = name[:i]
        name = proc.__module__.rsplit(".",1)[-1]+"."+name
        self.name = name

    def __repr__(self):
        self.resolve()
        res = f"{super().__repr__()}:{self.name}{self.a !r}"
        if self.kw:
            res += repr(self.kw)
        if self.result is not None:
            res += "/"+repr(self.result)
        return res

    def __str__(self):
        self.resolve()
        return f"{super().__str__()}::{self.name}"

class TTDResultError(TTDExecError):
    """
    This exception is used when a call to OpenTTD failed "late"; it
    encapsulates the internal command name.

    Don't catch this exception; catch `TTDExecError` instead.
    """
    def __init__(self,cmd,err):
        self.cmd = _ttd.enum.Command(cmd)
        super().__init__(err)

    def __repr__(self):
        self.resolve()
        return f"{super().__repr__()}:{self.cmd.name}"

    def __str__(self):
        self.resolve()
        return f"{super().__str__()}::{self.cmd.name}"

class TTDWrongTurn(TTDError):
    """You cn't turn more than that."""
    def __init__(self,a,b, reason):
        self.a = a
        self.b = b
        self.reason = reason

    def __repr__(self):
        return f"WrongTurn:{self.a !r}:{self.b !r}:{self.reason !r}"

    def __str__(self):
        return f"WrongTurn::{self.a.name}:{self.b.name}:{self.reason}"
