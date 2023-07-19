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

from __future__ import annotations

from enum import Enum
from functools import total_ordering, cache

__all__ = "Przedmioty",

from typing import cast


@total_ordering
class Przedmioty(Enum):
    """Enumeracja wszystkich przedmiotów szkolnych.
    Pierwszy string w wartości danego przedmiotu jest jego nazwą, drugi - domyślnym emoji (np. flagą),
    a pozostałe - alternatywnymi emoji (opcja do włączenia jako styl).

    W celu dostosowania przedmiotów, wystarczy zmienić jedynie poniższe definicje."""

    ANGIELSKI = "Angielski", "🇬🇧", "🇺🇸"
    POLSKI = "Polski", "🇵🇱"
    MATEMATYKA = "Matematyka", "🧮", "📏", "🔢", "🔠"
    RELIGIA = "Religia", "✝"
    INFORMATYKA = "Informatyka", "🖥️", "💻"
    NIEMIECKI = "Niemiecki", "🇩🇪"
    WF = "WF", "⚽", "🥅", "🤾‍", "🏀"
    HISTORIA = "Historia", "🏰"
    WYCHOWAWCZA = "Godzina wychowawcza", "✏️"
    CHEMIA = "Chemia", "🧪", "🧑‍🔬"
    FIZYKA = "Fizyka", "🛰️", "🔌"
    PRZEDSIEBIORCZOSC = "Przedsiębiorczość", "💰"
    BIOLOGIA = "Biologia", "🐟", "🍃"
    GEOGRAFIA = "Geografia", "🌍"

    def __reduce_ex__(self, protocol):
        """Pozwala na skuteczniejsze pamięciowo picklowanie przedmiotów poprzez zapamiętanie tylko nazwy"""
        return getattr, (self.__class__, self.name)

    def __lt__(self, inny):
        """Przedmiot jest mniejszy od drugiego, gdy jego nazwa alfabetycznie jest mniejsza"""
        return self.nazwa < inny.nazwa

    @property
    def nazwa(self) -> str:
        """Zwraca nazwę przedmiotu"""
        return self.value[0]

    @property
    def emoji(self) -> tuple[str]:
        """Zwraca listę (tuple) wszystkich emoji danego przedmiotu"""
        return self.value[1:]

    @classmethod
    @cache
    def lista(cls) -> dict[str, Przedmioty]:
        """Zwraca dict listy nazw (key) i przedmiotów o tej nazwie (value)"""
        return {cast(str, p.nazwa): p for p in cls}
