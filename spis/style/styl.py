from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from sortedcontainers import SortedList

from .opcje import *
from ..zadanie import *

__all__ = "Styl",


@dataclass(unsafe_hash=True)
class Styl(ABC):
    """Przechowuje ustawienia stylu wyświetlania spisu dla danego użytkownika"""

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
