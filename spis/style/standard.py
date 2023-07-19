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

import datetime
from logging import getLogger
from typing import Any

from sortedcontainers import SortedList

from .opcje import *
from .styl import *
from ..zadanie import Ogloszenie, ZadanieDomowe

logger = getLogger(__name__)

ZNACZNIK_UCIECIA_TEKSTU = "\n```\n...```"  # Symbolizuje osiągnięcie limitu 2000 znaków przy wyświetlaniu spisu


class StandardowyStyl(Styl):
    """Styl wyświetlania jako zwykły tekst z Markdownem"""

    def opracowanie_przy_zadaniu(self, zadanie: Ogloszenie) -> str | None:
        """Zwraca opracowanie wyświetlane przy zadaniu/ogłoszeniu, jeśli użytkownik ma je włączone"""
        if self.opracowanie == StylOpracowania.OBOK:
            return f"dodane przez: <@{zadanie.utworzono[0]}>"
        if self.opracowanie == StylOpracowania.OBOK_DATA:
            return f"dodane przez: <@{zadanie.utworzono[0]}> ({STYLE_DATY[self.data](zadanie.utworzono[1])[:-2]})"
        return None

    def formatuj_tresc_zadania(self, zadanie: ZadanieDomowe) -> str:
        """Formatuje samą treść zadania"""
        if self.nazwa_przedmiotu or self.emoji != "Nie wyświetlaj":  # Logika wyświetlania nazw i emoji przedmiotów
            emoji = STYLE_EMOJI[self.emoji](zadanie.przedmiot)
            wynik = f"**{emoji}{f'{zadanie.przedmiot.nazwa}{emoji}' if self.nazwa_przedmiotu else ''}**:"
        else:
            wynik = "-"
        opr = self.opracowanie_przy_zadaniu(zadanie)
        if self.id and opr:  # Tak zwane statystyki dla nerdów
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
        if self.id and opr:  # Tak zwane statystyki dla nerdów
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
        wynik = ""
        dzien = datetime.date.today() - datetime.timedelta(days=1)  # Do wypisywania dat w odpowiednich miejscach
        ogloszenia = False  # Czy w trakcie układania wyniku zaczęto już zapisywać ogłoszenia (zawsze po zadaniach)?
        problem_z_dlugoscia = False  # True, gdy w pewnym momencie układania spisu osiągnięto limit 2000 znaków
        for z in spis:
            if type(z) != ZadanieDomowe and not ogloszenia:  # Nagłówek ma być wypisany tylko raz
                ogloszenia = True
                wynik += "\nOgłoszenia:\n"
            if ogloszenia:  # Jeśli aktualny element spisu (i każdy kolejny) jest ogłoszeniem
                wynik += self.formatuj_tresc_ogloszenia(z) + "\n"
            else:
                zadanie = self.formatuj_tresc_zadania(z) + "\n"
                if (data_zadania := z.prawdziwy_termin.date()) > dzien:  # Dopisywanie dat
                    zadanie = STYLE_DATY[self.data](z.prawdziwy_termin) + zadanie
                    dzien = data_zadania
                wynik += zadanie
            if len(wynik) >= 2000:  # Ucięcie pętli, aby nie marnować czasu, gdy osiągnięto już i tak limit
                break
        if self.opracowanie == StylOpracowania.NA_DOLE:  # Dodanie opracowania z wszystkimi twórcami aktualnych zadań
            opracowanie = "\nOpracowanie spisu:\n"
            opracowanie += ", ".join({f"<@{z.utworzono[0]}>" for z in spis})  # Set comprehension
            if len(wynik) + len(opracowanie) < 2000:  # Znowu limity Discorda
                wynik += opracowanie
            else:
                problem_z_dlugoscia = True
        while len(wynik) >= (2000 - len(ZNACZNIK_UCIECIA_TEKSTU)):  # Dopóki nie zmieścimy zadań i znacznika ucięcia
            problem_z_dlugoscia = True
            wynik = wynik[:wynik.rfind("\n")]  # Ucinany wynik do momentu ostatniego wystąpienia nowej linijki
        if problem_z_dlugoscia:
            logger.debug("Przekroczono limit długości wyświetlania spisu!")
            wynik += ZNACZNIK_UCIECIA_TEKSTU
        return {"content": wynik}

    def formatuj_zadanie(self, naglowek: str, zadanie: ZadanieDomowe, *, wymus_id: bool = False) -> dict[str, Any]:
        if wymus_id:
            poprzednie_ustawienie_id = self.id
            self.id = True
            tresc = self.formatuj_tresc_zadania(zadanie)
            self.id = poprzednie_ustawienie_id
        else:
            tresc = self.formatuj_tresc_zadania(zadanie)
        return {"content": f"{naglowek}\n"
                           f"{STYLE_DATY[self.data](zadanie.prawdziwy_termin)}"
                           f"{tresc}"}

    def formatuj_ogloszenie(self, naglowek: str, ogloszenie: Ogloszenie, *, wymus_id: bool = False) -> dict[str, Any]:
        if wymus_id:
            poprzednie_ustawienie_id = self.id
            self.id = True
            tresc = self.formatuj_tresc_ogloszenia(ogloszenie)
            self.id = poprzednie_ustawienie_id
        else:
            tresc = self.formatuj_tresc_ogloszenia(ogloszenie)
        return {"content": f"{naglowek}\n\n{tresc}"}
