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

import re
from dataclasses import dataclass, field
from datetime import datetime
from functools import total_ordering
from logging import getLogger

from discord.ext import tasks

from .przedmiot import Przedmioty

__all__ = "Ogloszenie", "ZadanieDomowe"
logger = getLogger(__name__)

# Regex do znajdowania wszystkich linków w treści zadania
LINK_REGEX = re.compile(r"(https?://[a-zA-Z0-9-._~:/?#\[\]@!$&'()*+,;=%]*[a-zA-Z0-9-_~:/?#\[\]@!$&'()*+;=%])")


@total_ordering
@dataclass(eq=False, unsafe_hash=True)
class Ogloszenie:
    """Reprezentuje ogłoszenie wyświetlające się pod spisem"""

    termin_usuniecia: datetime
    tresc: str
    utworzono: tuple[int, datetime]  # Zawiera ID autora i datę utworzenia
    id: str = field(init=False, hash=False)
    task: tasks.Loop | None = field(init=False, hash=False, repr=False)

    @staticmethod
    def popraw_linki(tekst: str) -> str:
        """Poprawia podany tekst tak, aby linki nie generowały poglądów przy wypisywaniu spisu.
        Zasada działania: gdy link znajduje się w nawiasach ostrokątnych, nie generuje on embedów."""
        # \1 oznacza backtracking do 1 grupy każdego matcha, czyli do całego linku
        ret = LINK_REGEX.sub(r"<\1>", tekst)
        logger.debug(f'Poprawianie linków: {tekst!r} na {ret!r}')
        return ret

    def stworz_task(self):
        """Tworzy task, którego celem jest usunięcie danego zadania domowego po upłynięciu jego terminu"""
        termin = (self.termin_usuniecia - datetime.now()).total_seconds()
        if termin <= 0:  # Data w przeszłości
            self.task = None
            return

        # Wykonaj 2 razy, raz po utworzeniu, raz po upłynięciu czasu
        @tasks.loop(seconds=termin, count=2)
        async def usun_zadanie_po_terminie():
            if self.termin_usuniecia < datetime.now():  # Upewnij się, że to już czas
                logger.info(f'Automatycznie usunięto zadanie: {self!r}')
                from .main import bot
                bot.stan.lista_zadan.remove(self)

        usun_zadanie_po_terminie.start()  # Wystartuj task
        self.task = usun_zadanie_po_terminie

    def _wartosci_z_dicta_bez_taska(self) -> tuple:
        """Zwraca tuple wszystkich pól obiektu z wyłączeniem taska.
        Używane w pickle oraz w porównywaniu obiektów"""
        return tuple(v for k, v in self.__dict__.items() if k != "task")

    def __post_init__(self):
        """Inicjalizuje ID i tworzy task do usunięcia ogłoszenia"""
        self.tresc = self.popraw_linki(self.tresc)
        self.id = hex(abs(hash(self)))[2:]
        self.stworz_task()

    def __eq__(self, other) -> bool:
        """Porównuje to ogłoszenie z innym obiektem"""
        return type(self) == type(other) and self._wartosci_z_dicta_bez_taska() == other._wartosci_z_dicta_bez_taska()

    def __lt__(self, other) -> bool:
        """Służy głównie do sortowania ogłoszeń lub zadań domowych"""
        if type(self) != type(other):
            return type(self).__name__ > type(other).__name__  # Chcę, aby ogłoszenia znajdowały się na końcu spisu
        return self._wartosci_z_dicta_bez_taska() < other._wartosci_z_dicta_bez_taska()

    def __del__(self):
        """Przy destrukcji obiektu anuluje jego task"""
        if self.task is not None:
            self.task.cancel()

    def __getstate__(self) -> tuple:
        """Zapisuje w pickle wszystkie dane ogłoszenia oprócz taska"""
        return self._wartosci_z_dicta_bez_taska()

    def __setstate__(self, state: tuple):
        """Wczytuje stan obiektu z pickle"""
        self.termin_usuniecia, self.tresc, self.utworzono, self.id = state
        self.stworz_task()


@dataclass(eq=False, unsafe_hash=True)
class ZadanieDomowe(Ogloszenie):
    """Reprezentuje zadanie domowe posiadające dodatkowo przedmiot oprócz innych atrybutów ogłoszenia"""

    przedmiot: Przedmioty
    prawdziwy_termin: datetime  # Wyświetlany termin w zadaniu, zazwyczaj różni się od termin_usuniecia

    def __setstate__(self, state: tuple):
        """Wczytuje stan obiektu z pickle"""
        self.termin_usuniecia, self.tresc, self.utworzono, self.przedmiot, self.prawdziwy_termin, self.id = state
        self.stworz_task()
