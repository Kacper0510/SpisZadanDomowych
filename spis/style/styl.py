from dataclasses import dataclass

from .opcje import *


@dataclass
class Styl:
    """Przechowuje ustawienia stylu wyświetlania spisu dla danego użytkownika"""

    data: str = next(iter(STYLE_DATY))  # Sposób wyświetlania dat
    czas: str = next(iter(STYLE_CZASU))  # Sposób wyświetlania godziny zadania
    id: bool = False  # Wyświetlanie ID
    nazwa_przedmiotu: bool = True  # Wyświetlanie nazwy przedmiotu
    emoji: str = next(iter(STYLE_EMOJI))  # Sposób wyświetlania emoji przy przedmiocie
    opracowanie: str = STYLE_OPRACOWANIA[0]  # Sposób wyświetlania opracowania
