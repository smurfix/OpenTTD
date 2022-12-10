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
#include "string_func.h"
#include "querystring_gui.h"

// TODO SLOWPACE: Refactor to QueryString method may be?
static void SetEditBoxInt(QueryString& box, int v) {
    SetDParam(0, v);
    char *last_of = &box.text.buf[box.text.max_bytes - 1];
    GetString(box.text.buf, STR_JUST_INT, last_of);
	box.orig = stredup(box.text.buf);
}

// TODO SLOWPACE: Refactor to QueryString method may be?
static int GetEditBoxInt(const QueryString& box) {
    int v = atoi(box.text.buf);
    return v;
}

/** Window to select a custom pace factor */
struct SetPaceFactorWindow : Window {
	SetPaceFactorCallback *callback; ///< Callback to call when a pace factor has been seletect
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
		Window *parent,
		int initial_pace_factor,
		SetPaceFactorCallback *callback
	) :
			Window(desc),
			callback(callback),
			pace_factor(initial_pace_factor),
			hours_editbox(4),
			days_editbox(3)
	{
		this->parent = parent;

		if (pace_factor == 0) pace_factor = 1;

		int hours = (pace_factor / 4) % 24;
		int days = pace_factor / 4 / 24;

		InitEditBox(this->hours_editbox, WID_SPF_HOUR, hours);
		InitEditBox(this->days_editbox, WID_SPF_DAY, days);

		this->InitNested(WN_PACE_FACTOR);

		this->SetFocusedWidget(WID_SPF_MINUTE);
	}

	void InitEditBox(QueryString& box, int widget_id, int initialValue) {
		char *last_of = &box.text.buf[box.text.max_bytes - 1];
		SetDParam(0, initialValue);
		GetString(box.text.buf, STR_JUST_INT, last_of);
		StrMakeValidInPlace(box.text.buf, last_of, SVS_NONE);

		/* Make sure the name isn't too long for the text buffer in the number of
		 * characters (not bytes). max_chars also counts the '\0' characters. */
		while (Utf8StringLength(box.text.buf) + 1 > box.text.max_chars) {
			*Utf8PrevChar(box.text.buf + strlen(box.text.buf)) = '\0';
		}

		box.text.UpdateSize();

		if ((flags & QSF_ACCEPT_UNCHANGED) == 0) box.orig = stredup(box.text.buf);

		this->querystrings[widget_id] = &box;
		// box.caption = caption;
		box.cancel_button = WID_SPF_CANCEL;
		box.ok_button = WID_SPF_APPLY;
		box.text.afilter = CS_NUMERAL;
		this->flags = flags;
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
				for (int i = 0; i < 4; i++)
					list.emplace_back(new DropDownListParamStringItem(STR_PACE_FACTOR_MINUTE_0 + i, i, false));
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
			case WID_SPF_MINUTE: SetDParam(0, STR_PACE_FACTOR_MINUTE_0 + this->pace_factor % 4); break;
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

				if (this->callback != nullptr) this->callback(pace_factor);
				this->Close();
				break;
			}

			case WID_SPF_CANCEL: {
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
					SetMinimalSize(20, 12), SetResize(1, 0), SetFill(1, 0), SetPadding(2, 2, 2, 2),
					SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_DAY_TOOLTIP),
				NWidget(WWT_EDITBOX, COLOUR_BROWN, WID_SPF_HOUR),
					SetMinimalSize(20, 12), SetResize(1, 0), SetFill(1, 0), SetPadding(2, 2, 2, 2),
					SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_HOUR_TOOLTIP),
				NWidget(WWT_DROPDOWN, COLOUR_ORANGE, WID_SPF_MINUTE),
				    SetFill(1, 0), SetDataTip(STR_JUST_STRING, STR_PACE_FACTOR_MINUTE_TOOLTIP),
			EndContainer(),
			NWidget(NWID_HORIZONTAL),
				NWidget(NWID_SPACER), SetFill(1, 0),
				NWidget(WWT_CAPTION, COLOUR_BROWN, WID_SPF_ERROR_CAPTION), SetDataTip(STR_PACE_FACTOR_NON_ZERO_ERROR, STR_NULL),
				NWidget(NWID_SPACER), SetFill(1, 0),
			EndContainer(),
			NWidget(NWID_HORIZONTAL, NC_EQUALSIZE),
				NWidget(WWT_TEXTBTN, COLOUR_GREY, WID_SPF_CANCEL), SetMinimalSize(30, 12), SetFill(1, 1), SetDataTip(STR_BUTTON_CANCEL, STR_NULL),
				NWidget(WWT_TEXTBTN, COLOUR_GREY, WID_SPF_APPLY), SetMinimalSize(30, 12), SetFill(1, 1), SetDataTip(STR_BUTTON_OK, STR_NULL),
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
	int initial_pace_factor,
	SetPaceFactorCallback *callback
)
{
	CloseWindowByClass(WC_PACE_FACTOR);

	new SetPaceFactorWindow(
		&_set_pace_factor_desc,
		parent,
		initial_pace_factor,
		callback
	);
}
