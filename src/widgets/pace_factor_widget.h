/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file pace_factor_widget.h Types related to the pace factor window widgets. */

#ifndef WIDGETS_PACE_FACTOR_WIDGET_H
#define WIDGETS_PACE_FACTOR_WIDGET_H

/** Widgets of the #SetPaceFactorWindow class. */
enum SetPaceFactorWidgets {
	WID_SPF_DAY,              ///< Text field for the day.
	WID_SPF_HOUR,             ///< Text field for hour.
	WID_SPF_MINUTE,           ///< Dropdown for minute.
	WID_SPF_ERROR_PANEL,      ///< Error panel
	WID_SPF_APPLY,            ///< Apply pace factor
	WID_SPF_ERROR_CAPTION,    ///< If user tries to set invalid value (0)
};

#endif /* WIDGETS_PACE_FACTOR_WIDGET_H */
