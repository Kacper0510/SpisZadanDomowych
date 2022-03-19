from dataclasses import dataclass
from typing import Any

from sortedcontainers import SortedList

from .opcje import *
from .styl import *
from ..zadanie import Ogloszenie, ZadanieDomowe


@dataclass
class StandardowyStyl(Styl):
    """Styl wyświetlania jako zwykły tekst z Markdownem"""

    def opracowanie_przy_zadaniu(self, zadanie: Ogloszenie) -> str:
        """Zwraca opracowanie wyświetlane przy zadaniu/ogłoszeniu, jeśli użytkownik ma je włączone"""
        if self.opracowanie == "Przy każdym zadaniu":
            return f"dodane przez: <@{zadanie.utworzono[0]}>"
        elif self.opracowanie == "Przy każdym zadaniu (z datą utworzenia)":
            return f"dodane przez: <@{zadanie.utworzono[0]}> ({STYLE_DATY[self.data](zadanie.utworzono[1])[:-2]})"
        else:
            return ""

    def formatuj_tresc_zadania(self, zadanie: ZadanieDomowe) -> str:
        """Formatuje samą treść zadania"""
        if self.nazwa_przedmiotu or self.emoji != "Nie wyświetlaj":
            emoji = STYLE_EMOJI[self.emoji](zadanie.przedmiot)
            wynik = f"**{emoji}{f'{zadanie.przedmiot.nazwa}{emoji}' if self.nazwa_przedmiotu else ''}**:"
        else:
            wynik = "-"
        opr = self.opracowanie_przy_zadaniu(zadanie)
        if self.id and opr:
            wynik += f" [ID: {zadanie.id}, {opr}]"
        elif self.id:
            wynik += f" [ID: {zadanie.id}]"
        elif opr:
            wynik += f" [{opr}]"
        # Wypisywane tylko gdy czas był podany przy tworzeniu zadania
        if not (zadanie.prawdziwy_termin.hour == 0 and zadanie.prawdziwy_termin.minute == 0):
            wynik += STYLE_CZASU[self.czas](zadanie.prawdziwy_termin)
        return f"{wynik} {zadanie.tresc}"

    def formatuj_tresc_ogloszenia(self, ogloszenie: Ogloszenie) -> str:
        """Formatuje treść ogłoszenia, aby uzwględnić dodatkowe informacje"""
        opr = self.opracowanie_przy_zadaniu(ogloszenie)
        if self.id and opr:
            wynik = f"[ID: {ogloszenie.id}, {opr}] "
        elif self.id:
            wynik = f"[ID: {ogloszenie.id}] "
        elif opr:
            wynik = f"[{opr}] "
        else:
            wynik = ""
        return wynik + ogloszenie.tresc

    def formatuj_spis(self, spis: SortedList[Ogloszenie]) -> dict[str, Any]:
        if len(spis) == 0:
            return {"content": "Spis jest aktualnie pusty!"}
        return {"content": "\n".join(self.formatuj_tresc_zadania(z) for z in spis)}  # FIXME

    def formatuj_zadanie(self, naglowek: str, zadanie: ZadanieDomowe) -> dict[str, Any]:
        return {"content": f"> {naglowek}\n"
                           f"{STYLE_DATY[self.data](zadanie.prawdziwy_termin)}"
                           f"{self.formatuj_tresc_zadania(zadanie)}"}

    def formatuj_ogloszenie(self, naglowek: str, ogloszenie: Ogloszenie) -> dict[str, Any]:
        return {"content": f"> {naglowek}\n\n{self.formatuj_tresc_ogloszenia(ogloszenie)}"}
