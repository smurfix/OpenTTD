#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
Callbacks for the OpenTTD adapter
"""

from __future__ import annotations

import sys

from ._main import _storage, _main

def storage_hook():
    """
    Fetch the current data object.
    """
    return _storage.get()

