/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file pace_factor_gui.cpp Graphical selection of custom pace factor. */

#include "stdafx.h"
#include "strings_func.h"
#include "date_func.h"
#include "window_func.h"
#include "window_gui.h"
#include "pace_factor_gui.h"
#include "core/geometry_func.hpp"

#include "widgets/dropdown_type.h"
#include "widgets/pace_factor_widget.h"

#include "safeguards.h"
#include "querystring_gui.h"

// TODO SLOWPACE: Refactor to QueryString method may be?
static void SetEditBoxInt(QueryString& box, int v) {
    SetDParam(0, v);
    char *last_of = &box.text.buf[box.text.max_bytes - 1];
    GetString(box.text.buf, STR_JUST_INT, last_of);
}

// TODO SLOWPACE: Refactor to QueryString method may be?
static int GetEditBoxInt(const QueryString& box) {
    int v = atoi(box.text.buf);
    return v;
}

/** Window to select a custom pace factor */
struct SetPaceFactorWindow : Window {
	SetPaceFactorCallback *callback; ///< Callback to call when a pace factor has been seletect
	void *callback_data;             ///< Callback data pointer.
	int pace_factor_minutes;         ///< Storage for minutes fractures of game year
	int pace_factor;                 ///< Pace factor value
	QueryString hours_editbox;               ///< Subwidget of hours edit field
	QueryString days_editbox;                ///< Subwidget of days edit field

	/**
	 * Create the new 'set date' window
	 * @param desc the window description
	 * @param window_number number of the window
	 * @param parent the parent window, i.e. if this closes we should close too
	 * @param initial_pace_factor the initial pace factor value
	 * @param callback the callback to call once a pace factor has been selected
	 */
	SetPaceFactorWindow(
		WindowDesc *desc,
		WindowNumber window_number,
		Window *parent,
		int initial_pace_factor,
		SetPaceFactorCallback *callback,
		void *callback_data
	) :
			Window(desc),
			callback(callback),
			callback_data(callback_data),
			pace_factor(initial_pace_factor),
			hours_editbox(4),
			days_editbox(3)
	{
		this->parent = parent;
		this->InitNested(window_number);

		this->querystrings[WID_SPF_HOUR] = &this->hours_editbox;
		this->querystrings[WID_SPF_DAY] = &this->days_editbox;

		this->hours_editbox.text.afilter = CS_NUMERAL;
		this->days_editbox.text.afilter = CS_NUMERAL;

		if (pace_factor == 0) pace_factor = 1;

		int hours = (pace_factor / 4) % 24;
		int days = pace_factor / 4 / 24;

		SetEditBoxInt(this->hours_editbox, hours);
		SetEditBoxInt(this->days_editbox, days);
	}


	Point OnInitialPosition(int16 sm_width, int16 sm_height, int window_number) override
	{
		Point pt = { this->parent->left + this->parent->width / 2 - sm_width / 2, this->parent->top + this->parent->height / 2 - sm_height / 2 };
		return pt;
	}

	/**
	 * Helper function to construct the dropdown.
	 * @param widget the dropdown widget to create the dropdown for
	 */
	void ShowDropDown(int widget)
	{
		int selected;
		DropDownList list;

		switch (widget) {
			default: NOT_REACHED();
			case WID_SPF_MINUTE:
				for (int i = 0; i < 60; i++) {
					auto *item = new DropDownListParamStringItem(STR_PACE_FACTOR_MINUTE_0, i, false);
					item->SetParam(0, i);
					list.emplace_back(item);
				}
				// In minutes drop-down we hold 0, 15, 30, or 45 values, in our
				// case it is a remainder after division by 4.
				selected = this->pace_factor_minutes % 4;
				break;
		}

		ShowDropDownList(this, std::move(list), selected, widget);
	}

	void UpdateWidgetSize(int widget, Dimension *size, const Dimension &padding, Dimension *fill, Dimension *resize) override
	{
		Dimension d = {0, 0};
		switch (widget) {
			default: return;
			case WID_SPF_MINUTE:
				SetDParamMaxValue(0, 59);
				d = maxdim(d, GetStringBoundingBox(STR_JUST_INT));
				break;

			case WID_SPF_HOUR:
				SetDParamMaxValue(0, 4369);
				d = maxdim(d, GetStringBoundingBox(STR_JUST_INT));
				break;

			case WID_SPF_DAY:
				SetDParamMaxValue(0, 183);
				d = maxdim(d, GetStringBoundingBox(STR_JUST_INT));
				break;
		}

		d.width += padding.width;
		d.height += padding.height;
		*size = d;
	}

	void SetStringParameters(int widget) const override
	{
		switch (widget) {
			case WID_SPF_MINUTE: SetDParam(0, this->pace_factor % 4); break;

			// FIXME SLOWPACE: I think these two will never happen
			case WID_SPF_HOUR: SetDParam(0, (this->pace_factor / 4) % 24); break;
			case WID_SPF_DAY:   SetDParam(0, this->pace_factor / (4*24)); break;
		}
	}

	void OnClick(Point pt, int widget, int click_count) override
	{
		switch (widget) {
			case WID_SPF_MINUTE:
				ShowDropDown(widget);
				break;

			case WID_SPF_APPLY: {
				int pace_factor =
					this->pace_factor_minutes
					+ GetEditBoxInt(this->hours_editbox) * 4
					+ GetEditBoxInt(this->days_editbox) * 4 * 24;

				if (this->callback != nullptr) this->callback(this, this->callback_data, pace_factor);
				this->Close();
				break;
			}
		}
	}

	void OnDropdownSelect(int widget, int index) override
	{
		switch (widget) {
			case WID_SPF_MINUTE:
				this->pace_factor_minutes = index;
				break;
		}
		this->SetDirty();
	}
};

/** Widgets for the date setting window. */
static const NWidgetPart _nested_set_pace_factor_widgets[] = {
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_CLOSEBOX, COLOUR_BROWN),
		NWidget(WWT_CAPTION, COLOUR_BROWN), SetDataTip(STR_PACE_FACTOR_CAPTION, STR_TOOLTIP_WINDOW_TITLE_DRAG_THIS),
	EndContainer(),
	NWidget(WWT_PANEL, COLOUR_BROWN),
		NWidget(NWID_VERTICAL), SetPIP(6, 6, 6),
			NWidget(NWID_HORIZONTAL, NC_EQUALSIZE), SetPIP(6, 6, 6),
				NWidget(WWT_EDITBOX, COLOUR_BROWN, WID_SPF_DAY),
					SetMinimalSize(80, 12), SetResize(1, 0), SetFill(1, 0), SetPadding(2, 2, 2, 2),
					SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_DAY_TOOLTIP),
				NWidget(WWT_EDITBOX, COLOUR_BROWN, WID_SPF_HOUR),
					SetMinimalSize(80, 12), SetResize(1, 0), SetFill(1, 0), SetPadding(2, 2, 2, 2),
					SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_HOUR_TOOLTIP),
				NWidget(WWT_DROPDOWN, COLOUR_ORANGE, WID_SPF_MINUTE),
				    SetFill(1, 0), SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_MINUTE_TOOLTIP),
			EndContainer(),
			NWidget(NWID_HORIZONTAL),
				NWidget(NWID_SPACER), SetFill(1, 0),
				NWidget(WWT_CAPTION, COLOUR_RED, WID_SPF_ERROR_CAPTION), SetDataTip(STR_WHITE_STRING, STR_NULL),
				NWidget(NWID_SPACER), SetFill(1, 0),
			EndContainer(),
			NWidget(NWID_HORIZONTAL),
				NWidget(NWID_SPACER), SetFill(1, 0),
				NWidget(WWT_CAPTION, COLOUR_RED, WID_SPF_ERROR_CAPTION), SetDataTip(STR_WHITE_STRING, STR_NULL),
				NWidget(WWT_PUSHTXTBTN, COLOUR_BROWN, WID_SPF_APPLY), SetMinimalSize(100, 12), SetDataTip(STR_PACE_FACTOR_APPLY, STR_PACE_FACTOR_APPLY_TOOLTIP),
				NWidget(NWID_SPACER), SetFill(1, 0),
			EndContainer(),
		EndContainer(),
	EndContainer()
};

/** Description of the date setting window. */
static WindowDesc _set_pace_factor_desc(
	WDP_CENTER, nullptr, 0, 0,
	WC_PACE_FACTOR, WC_NONE,
	0,
	_nested_set_pace_factor_widgets, lengthof(_nested_set_pace_factor_widgets)
);

/**
 * Create the new 'set date' window
 * @param window_number number for the window
 * @param parent the parent window, i.e. if this closes we should close too
 * @param initial_date the initial date to show
 * @param min_year the minimum year to show in the year dropdown
 * @param max_year the maximum year (inclusive) to show in the year dropdown
 * @param callback the callback to call once a date has been selected
 * @param callback_data extra callback data
 */
void ShowSetPaceFactorWindow(
	Window *parent,
	int window_number,
	int initial_pace_factor,
	SetPaceFactorCallback *callback,
	void *callback_data
)
{
	CloseWindowByClass(WC_PACE_FACTOR);

	new SetPaceFactorWindow(
		&_set_pace_factor_desc,
		window_number,
		parent,
		initial_pace_factor,
		callback,
		callback_data
	);
}
