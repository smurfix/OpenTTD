#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
Fake a _ttd module for testing
"""

from __future__ import annotations

import sys

__all__ = ["_ttd"]

try:
	from .data import _ttd
except ImportError:
	print("""\
The module 'openttd._stub.data' could not be loaded.
Most probably it doesn't exist.

To fix this: Run 'openttd -Y openttd._stub_export'.
""", file=sys.stderr)
	raise RuntimeError("No _ttd stub found.")

sys.modules["_ttd"] = _ttd
