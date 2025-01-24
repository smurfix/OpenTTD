/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file sign_widget.h Types related to the sign widgets. */

#ifndef WIDGETS_PYTHON_WIDGET_H
#define WIDGETS_PYTHON_WIDGET_H

/** Widgets of the #SignListWindow class. */
enum PyScriptListWidgets : WidgetID {
	WID_PYL_CAPTION,               ///< Caption of the window.
	WID_PYL_LIST,                  ///< List of signs.
	WID_PYL_SCROLLBAR,             ///< Scrollbar of list.
};

#endif /* WIDGETS_PYTHON_WIDGET_H */
