/*
 * This file is part of OpenTTD.
 * OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
 * OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
 */

/** @file python_gui.cpp The GUI for Python scripts. */

#include "stdafx.h"
#include "company_gui.h"
#include "company_func.h"
#include "signs_base.h"
#include "signs_func.h"
#include "debug.h"
#include "command_func.h"
#include "strings_func.h"
#include "window_func.h"
#include "map_func.h"
#include "viewport_func.h"
#include "querystring_gui.h"
#include "sortlist_type.h"
#include "stringfilter_type.h"
#include "string_func.h"
#include "core/geometry_func.hpp"
#include "hotkeys.h"
#include "transparency.h"
#include "gui.h"
#include "signs_cmd.h"
#include "timer/timer.h"
#include "timer/timer_window.h"

#include "widgets/python_widget.h"

#include "table/strings.h"
#include "table/sprites.h"

#include "python/call_py.hpp"

#include "safeguards.h"

struct PyScriptList {
	/**
	 * A GUIList with active Python scripts
	 */
	typedef GUIList<PyTTD::Script, std::nullptr_t, StringFilter &> GUIPyScriptList;

	GUIPyScriptList scripts;

	/**
	 * Creates a PyScriptList with filtering disabled by default.
	 */
	PyScriptList() { }

	void BuildScriptList()
	{
		if (!this->scripts.NeedRebuild()) return;

		Debug(misc, 3, "Building Python script list");

		this->scripts.clear();
		auto data = PyTTD::Script::GetIndices();

		this->scripts.reserve(data.size());

		for (unsigned int si : data) {
			PyTTD::Script *scr = PyTTD::Script::GetIfValid(si);
			if(scr == nullptr)
				continue;
			this->scripts.push_back(*scr);
		}
		this->scripts.RebuildDone();
	}

};

struct PyScriptListWindow : Window, PyScriptList {
	int text_offset; ///< Offset of the sign text relative to the left edge of the WID_PYL_LIST widget.
	Scrollbar *vscroll;

	PyScriptListWindow(WindowDesc &desc, WindowNumber window_number) : Window(desc)
	{
		this->CreateNestedTree();
		this->vscroll = this->GetScrollbar(WID_PYL_SCROLLBAR);
		this->FinishInitNested(window_number);

		/* Create initial list. */
		this->scripts.ForceRebuild();
	}

	void OnPaint() override
	{
		if (!this->IsShaded() && this->scripts.NeedRebuild()) {
			this->BuildScriptList();
			this->vscroll->SetCount(this->scripts.size());
		}
		this->DrawWidgets();
	}

	void DrawWidget(const Rect &r, WidgetID widget) const override
	{
		switch (widget) {
			case WID_PYL_LIST: {
				Rect tr = r.Shrink(WidgetDimensions::scaled.framerect);
				uint text_offset_y = (this->resize.step_height - GetCharacterHeight(FS_NORMAL) + 1) / 2;

				/* No scripts? */
				if (this->vscroll->GetCount() == 0) {
					DrawString(tr.left, tr.right, tr.top + text_offset_y, STR_STATION_LIST_NONE);
					return;
				}

				/* At least one script available. */
				auto [first, last] = this->vscroll->GetVisibleRangeIterators(this->scripts);
				for (auto it = first; it != last; ++it) {
					SetDParam(0, it->id);
					DrawString(tr.left, tr.right, tr.top + text_offset_y, STR_PYSCRIPT_NAME, TC_YELLOW);
					tr.top += this->resize.step_height;
				}
				break;
			}
		}
	}

	void SetStringParameters(WidgetID widget) const override
	{
		if (widget == WID_PYL_CAPTION) SetDParam(0, this->vscroll->GetCount());
	}

	void OnClick([[maybe_unused]] Point pt, WidgetID widget, [[maybe_unused]] int click_count) override
	{
		switch (widget) {
			case WID_PYL_LIST: {
				auto it = this->vscroll->GetScrolledItemFromWidget(this->scripts, pt.y, this, WID_PYL_LIST, WidgetDimensions::scaled.framerect.top);
				if (it == this->scripts.end()) return;

				// const PyTTD::Script *si = it;
				// TODO open params window, offer to cancel, etc.
				break;
			}
		}
	}

	void OnResize() override
	{
		this->vscroll->SetCapacityFromWidget(this, WID_PYL_LIST, WidgetDimensions::scaled.framerect.Vertical());
	}

	void UpdateWidgetSize(WidgetID widget, Dimension &size, [[maybe_unused]] const Dimension &padding, [[maybe_unused]] Dimension &fill, [[maybe_unused]] Dimension &resize) override
	{
		switch (widget) {
			case WID_PYL_LIST: {
				Dimension spr_dim = GetSpriteSize(SPR_COMPANY_ICON);
				this->text_offset = WidgetDimensions::scaled.frametext.left + spr_dim.width + 2; // 2 pixels space between icon and the sign text.
				resize.height = std::max<uint>(GetCharacterHeight(FS_NORMAL), spr_dim.height + 2);
				Dimension d = {(uint)(this->text_offset + WidgetDimensions::scaled.frametext.right), padding.height + 5 * resize.height};
				size = maxdim(size, d);
				break;
			}

			case WID_PYL_CAPTION:
				SetDParamMaxValue(0, Sign::GetPoolSize(), 3);
				size = GetStringBoundingBox(STR_PYSCRIPT_LIST_CAPTION);
				size.height += padding.height;
				size.width  += padding.width;
				break;
		}
	}

	EventState OnHotkey([[maybe_unused]] int hotkey) override
	{
		return ES_NOT_HANDLED;
	}

	void MaybeBuildScriptList()
	{
		if (this->scripts.NeedRebuild()) {
			this->BuildScriptList();
			this->vscroll->SetCount(this->scripts.size());
			this->SetWidgetDirty(WID_PYL_CAPTION);
		}
	}

	/** Resort the sign listing on a regular interval. */
	IntervalTimer<TimerWindow> rebuild_interval = {std::chrono::seconds(3), [this](auto) {
		this->MaybeBuildScriptList();
		this->SetDirty();
	}};

	/**
	 * Some data on this window has become invalid.
	 * @param data Information about the changed data.
	 * @param gui_scope Whether the call is done from GUI scope. You may not do everything when not in GUI scope. See #InvalidateWindowData() for details.
	 */
	void OnInvalidateData([[maybe_unused]] int data = 0, [[maybe_unused]] bool gui_scope = true) override
	{
		/* When there is a filter string, we always need to rebuild the list even if
		 * the amount of scripts in total is unchanged, as the subset of scripts that is
		 * accepted by the filter might has changed. */
		if (data == 0 || data == -1) { // New or deleted script
			/* This needs to be done in command-scope to enforce rebuilding before resorting invalid data */
			this->scripts.ForceRebuild();
		}
	}
};

static constexpr NWidgetPart _nested_script_list_widgets[] = {
	NWidget(NWID_HORIZONTAL),
		NWidget(WWT_CLOSEBOX, COLOUR_BROWN),
		NWidget(WWT_CAPTION, COLOUR_BROWN, WID_PYL_CAPTION), SetDataTip(STR_PYSCRIPT_LIST_CAPTION, STR_TOOLTIP_WINDOW_TITLE_DRAG_THIS),
		NWidget(WWT_SHADEBOX, COLOUR_BROWN),
		NWidget(WWT_DEFSIZEBOX, COLOUR_BROWN),
		NWidget(WWT_STICKYBOX, COLOUR_BROWN),
	EndContainer(),
	NWidget(NWID_HORIZONTAL),
		NWidget(NWID_VERTICAL),
			NWidget(WWT_PANEL, COLOUR_BROWN, WID_PYL_LIST), SetMinimalSize(WidgetDimensions::unscaled.frametext.Horizontal() + 16 + 255, 0),
								SetResize(1, 1), SetFill(1, 0), SetScrollbar(WID_PYL_SCROLLBAR), EndContainer(),
		EndContainer(),
		NWidget(NWID_VERTICAL),
			NWidget(NWID_VSCROLLBAR, COLOUR_BROWN, WID_PYL_SCROLLBAR),
			NWidget(WWT_RESIZEBOX, COLOUR_BROWN),
		EndContainer(),
	EndContainer(),
};

static WindowDesc _script_list_desc(
	WDP_AUTO, "list_scripts", 358, 138,
	WC_PYSCRIPT_LIST, WC_NONE,
	0,
	_nested_script_list_widgets,
	nullptr // hotkeys
);

/**
 * Open the script list window
 *
 * @return newly opened script list window, or nullptr if the window could not be opened.
 */
Window *ShowPythonScriptList()
{
	return AllocateWindowDescFront<PyScriptListWindow>(_script_list_desc, 0);
}

/**
 * Handle clicking on a script.
 * @param si The sign that was clicked on.
 */
#if 0
void HandleClickOnScript(const PyTTD::Script *si)
{
	// TODO
}
#endif
