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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sortedcontainers import SortedList

from .opcje import *
from ..zadanie import *

__all__ = "Styl",


@dataclass(unsafe_hash=True)
class Styl(ABC):
    """Przechowuje ustawienia stylu wyświetlania spisu dla danego użytkownika

    Ta funkcja nie została nigdy w pełni zaimplementowana i udostępniona dla użytkowników w postaci komendy,
    lecz formatowanie zadań działa poprawnie. Z tego powodu, aby zmienić styl wyświetlania,
    należy edytować manualnie plik pickle lub zmienić globalny (domyślny) styl poniżej."""

    data: str = next(iter(STYLE_DATY))  # Sposób wyświetlania dat
    czas: str = next(iter(STYLE_CZASU))  # Sposób wyświetlania godziny zadania
    id: bool = False  # Wyświetlanie ID
    nazwa_przedmiotu: bool = True  # Wyświetlanie nazwy przedmiotu
    emoji: str = next(iter(STYLE_EMOJI))  # Sposób wyświetlania emoji przy przedmiocie
    opracowanie: StylOpracowania = StylOpracowania.NA_DOLE  # Sposób wyświetlania opracowania

    @abstractmethod
    def formatuj_spis(self, spis: SortedList[Ogloszenie]) -> dict[str, Any]:
        pass

    @abstractmethod
    def formatuj_zadanie(self, naglowek: str, zadanie: ZadanieDomowe, *, wymus_id: bool = False) -> dict[str, Any]:
        pass

    @abstractmethod
    def formatuj_ogloszenie(self, naglowek: str, ogloszenie: Ogloszenie, *, wymus_id: bool = False) -> dict[str, Any]:
        pass
