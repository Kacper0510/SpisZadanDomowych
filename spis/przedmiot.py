from __future__ import annotations

from enum import Enum
from functools import total_ordering, cache

__all__ = "Przedmioty",

from typing import cast


@total_ordering
class Przedmioty(Enum):
    """Enumeracja wszystkich przedmiotów szkolnych.
    Pierwszy string w wartości danego przedmiotu jest jego nazwą, drugi - ogólnodostępnym emoji (np. flagą),
    a pozostałe - customowymi emoji, np. z twarzą nauczyciela."""

    ANGIELSKI = "Angielski", "🇬🇧"
    POLSKI = "Polski", "🇵🇱"
    MATEMATYKA = "Matematyka", "🧮", "📏"
    RELIGIA = "Religia", "✝"
    MATMA_UZUP = "Matematyka uzupełniająca", "🔢", "🔠"
    INFA_RACZEK = "Informatyka (Raczek)", "🖥️"
    INFA_HERMA = "Informatyka (Herma)", "💻"
    NIEMIECKI_BABICZ = "Niemiecki (Babicz)", "🇩🇪"
    NIEMIECKI_SYCH = "Niemiecki (Sych)", "🇩🇪"
    WF = "WF", "⚽", "🥅", "🤾‍", "🏀"
    CHEMIA = "Chemia", "🧪", "🧑‍🔬"
    FIZYKA = "Fizyka", "🛰️", "🔌"
    HISTORIA = "Historia", "🏰"
    PRZEDSIEBIORCZOSC = "Przedsiębiorczość", "💰"
    ANGIELSKI_UZUP = "Angielski uzupełniający", "🇺🇸"
    BIOLOGIA = "Biologia", "🐟", "🍃"
    GEOGRAFIA = "Geografia", "🌍"
    WYCHOWAWCZA = "Godzina wychowawcza", "✏️"
    INNY = "Inne", "❓"

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
