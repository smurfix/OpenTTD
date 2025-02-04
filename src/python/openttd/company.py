#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module contails support for companies.
"""

from __future__ import annotations

import _ttd

import openttd
from .util import PlusSet
import enum
from attrs import define,field
from openttd._util import _Sub,with_
from openttd.util import extension_of
from ._support.id import _ID
from .base import SELF

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable,Self,Iterable

    Money = _ttd.support.Money


@extension_of(_ttd.script.company.Quarter)
class Quarter(_ID,int):
    pass

@extension_of(_ttd.script.company.Gender)
class Gender(_ID,int):
    pass

@extension_of(_ttd.script.company.LiveryScheme)
class LiveryScheme(_ID,int):
    pass

@extension_of(_ttd.script.company.Colours)
class Colour(_ID,int):
    pass
Color = Colour

@extension_of(_ttd.script.company.ExpensesType)
class Expenses(_ID,int):
    pass

@extension_of(_ttd.support.CompanyID)
class Company(_ID,int):
    def __new__(cls, id, raw=False):
        if raw:
            nid = id
        else:
            nid = _ttd.script.company.resolve_company_id(id)
            if nid == Company.INVALID:
                raise ValueError(id)
        return _ID.__new__(cls, int(nid))

    def __getattr__(self,k):
        return type(self)(getattr(_ttd.support.CompanyID,k))

    @property
    def _(self):
        breakpoint()
        return _ttd.support.CompanyID(int(self))

    @staticmethod
    def is_valid(id) -> bool:
        return _ttd.script.company.resolve_company_id(_ttd.support.CompanyID(id)) != Company.INVALID

    @property
    def is_mine(self):
        return _ttd.script.company.is_mine(self)

    def for_str(self) -> Iterable[str]:
        return int(self),self.name,

    def for_repr(self) -> Iterable[str]:
        return int(self),

    def _chk(self, err, rd=False):
        if SELF.get().company != self:
            raise ValueError(f"You can only {'change' if rd else 'access'} your own {err}")


    @property
    def name(self) -> str|None:
        return _ttd.script.company.get_name(self)

    def set_name(self, name: str) -> None:
        self._chk("company name")
        return with_(None, _ttd.script.company.set_name, openttd.Text(name))

    @property
    def president_name(self) -> str|None:
        return _ttd.script.company.get_president_name(self)

    def set_president_name(self, name: str) -> None:
        self._chk("president's name")
        return with_(None, _ttd.script.company.set_president_name, openttd.Text(name))

    @property
    def gender(self) -> str|None:
        self._chk("president's gender")
        return _ttd.script.company.get_gender(self)

    def set_gender(self, gender: Gender) -> None:
        return with_(None, _ttd.script.company.set_gender, gender)


    def set_loan_amount(self, amount: Money) -> None:
        self._chk("loan amount")
        return with_(None, _ttd.script.company.set_loan_amount, amount)

    def set_min_loan_amount(self, amount: Money) -> None:
        self._chk("minimum loan amount")
        return with_(None, _ttd.script.company.set_minimum_loan_amount, amount)

    @property
    def loan_amount(self) -> Money:
        self._chk("loan amount",True)
        return _ttd.script.company.get_loan_amount()

    @property
    def max_loan_amount(self) -> Money:
        self._chk("max loan amount",True)
        return _ttd.script.company.get_max_loan_amount()

    def set_max_loan_amount(self, amount: Money) -> None:
        return with_(None, _ttd.script.company.set_max_loan_amount_for_company, self, amount)

    def reset_max_loan_amount(self) -> None:
        return with_(None, _ttd.script.company.reset_max_loan_amount_for_company, self)

    @property
    def loan_interval(self) -> Money:
        self._chk("loan interval",True)
        return _ttd.script.company.get_loan_interval()

    @property
    def bank_balance(self) -> Money:
        return _ttd.script.company.get_bank_balance(self)

    def set_bank_balance(self, amount: Money) -> None:
        return with_(None, _ttd.script.company.change_bank_balance, self, amount)

    def quarterly_income(self, quarter: Quarter) -> Money:
        return _ttd.script.company.get_quarterly_income(self, quarter)

    def quarterly_expenses(self, quarter: Quarter) -> int:
        return _ttd.script.company.get_quarterly_expenses(self, quarter)

    def quarterly_cargo_delivered(self, quarter: Quarter) -> int:
        return _ttd.script.company.get_quarterly_expenses(self, quarter)

    def quarterly_performance_rating(self, quarter: Quarter) -> int:
        return _ttd.script.company.get_quarterly_performance_rating(self, quarter)

    def quarterly_company_value(self, quarter: Quarter) -> Money:
        return _ttd.script.company.get_quarterly_company_value(self, quarter)

    @property
    def hq_location(self, quarter: Quarter) -> Tile:
        return _ttd.script.company.get_company_hq(self, quarter)

    # Building it is on the Tile.

    def set_auto_renew_status(self, autorenew: bool) -> None:
        self._chk("autorenew status")
        return with_(None, _ttd.script.company.set_auto_renew_status, self, autorenew)

    @property
    def auto_renew_status(self) -> bool:
        return _ttd.script.company.get_auto_renew_status(self)

    def set_auto_renew_months(self, months: int) -> None:
        self._chk("autorenew months")
        return with_(None, _ttd.script.company.set_auto_renew_months, self, months)

    @property
    def auto_renew_months(self) -> int:
        return _ttd.script.company.get_auto_renew_months(self)

    def set_auto_renew_money(self, money: Money) -> None:
        self._chk("autorenew money")
        return with_(None, _ttd.script.company.set_auto_renew_money, self, money)

    @property
    def auto_renew_money(self) -> int:
        return _ttd.script.company.get_auto_renew_money(self)

    def livery_colours(self, scheme:LiveryScheme) -> tuple[LiveryColour, LiveryColour]:
        self._chk("livery colours",True)
        return (
            _ttd.script.company.get_primary_livery_colour(scheme),
            _ttd.script.company.get_secondary_livery_colour(scheme),
        )

    def set_livery_colours(self, scheme: LiveryScheme, primary: Colour|None = None, secondary: Colour|None = None) -> None:
        self._chk("livery colours")
        if primary is not None and primary != Colour.INVALID:
            with_(None, _ttd.script.company.set_primary_livery_colour, scheme, primary)
        if secondary is not None and secondary != Colour.INVALID:
            with_(None, _ttd.script.company.set_secondary_livery_colour, scheme, secondary)

def _gen_companies():
    id = int(Company.FIRST)
    while id <= int(Company.LAST):
        if not Company.is_valid(id):
            break
        yield Company(id)
        id += 1

class Companies(PlusSet[Company]):
    def __init__(self, source:Iterable[Sign|int]=None):
        if source is None:
            source = _gen_companies()
        for t in source:
            self.add(t)

Company.List = staticmethod(Companies)
