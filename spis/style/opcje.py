#  MIT License
#
#  Copyright (c) 2023 Kacper Wojciuch
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import random
from datetime import datetime, date
from enum import Enum
from typing import Callable

from ..date_parser import PolskiDateParser
from ..przedmiot import Przedmioty

__all__ = "STYLE_DATY", "STYLE_CZASU", "STYLE_EMOJI", "StylOpracowania"

STYLE_DATY: dict[str, Callable[[datetime], str]] = {
    "Zwykły tekst (domyślny)": lambda d: f"\n{PolskiDateParser.WEEKDAYS[d.weekday()][1].capitalize()}, "
                                         f"{d.day} {PolskiDateParser.MONTHS[d.month - 1][1]}"
                                         f"{f' {rok}' if (rok := d.year) != date.today().year else ''}:\n",
    "Formatowanie Discorda": lambda d: f"\n<t:{round(d.timestamp())}:D>:\n",
    "Data i dzień tygodnia": lambda d: f"\n<t:{round(d.timestamp())}:F>:\n",
    "Krótka data": lambda d: f"\n<t:{round(d.timestamp())}:d>:\n",
    "Relatywnie": lambda d: f"\n<t:{round(d.timestamp())}:R>:\n",
    "Nie wyświetlaj daty": lambda d: ""
}

STYLE_CZASU: dict[str, Callable[[datetime], str]] = {
    "Zwykły tekst (domyślny)": lambda d: f' *({d.hour}:{d.minute:02})* ',
    "Formatowanie Discorda": lambda d: f' (<t:{round(d.timestamp())}:t>)',
    "Nie wyświetlaj czasu": lambda d: ""
}

STYLE_EMOJI: dict[str, Callable[[Przedmioty], str]] = {
    "Zwykłe (domyślne)": lambda p: p.emoji[0],
    "Losowe": lambda p: random.choice(p.emoji),
    "Nie wyświetlaj": lambda p: ""
}


class StylOpracowania(Enum):
    NA_DOLE = "Pod spisem (domyślnie)"
    OBOK = "Przy każdym zadaniu"
    OBOK_DATA = "Przy każdym zadaniu (z datą utworzenia)"
    BRAK = "Nie wyświetlaj opracowania"

    def __reduce_ex__(self, protocol):
        """Pozwala na skuteczniejsze pamięciowo picklowanie poprzez zapamiętanie tylko nazwy"""
        return getattr, (self.__class__, self.name)
