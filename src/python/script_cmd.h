/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file script_cmd.h Command definitions related to scripts. */

#ifndef PY_SCRIPT_CMD_H
#define PY_SCRIPT_CMD_H

#include "../command_type.h"
#include "../tile_type.h"

CommandCallback PyCmdCB;
void CcPython(const CommandCost &result, TileIndex, uint32_t p1, uint32_t p2, uint64_t p3, uint32_t cmd);

#endif /* PY_SCRIPT_CMD_H */
