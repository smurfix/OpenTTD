/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file pace_factor_gui.h Graphical selection of custom pace factor. */

#ifndef PACE_FACTOR_H
#define PACE_FACTOR_H

#include "window_type.h"
#include <functional>

/**
 * Callback for when a pace factor has been set
 * @param w the window that sends the callback
 * @param pace_factor the date that has been chosen
 */
using SetPaceFactorCallback = std::function<void(int)>;

void ShowSetPaceFactorWindow(
	Window *parent,
	int initial_pace_factor,
	SetPaceFactorCallback&& callback
);

#endif /* PACE_FACTOR_H */
