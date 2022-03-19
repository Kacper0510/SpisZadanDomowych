import random
from datetime import datetime, date
from typing import Callable

from ..date_parser import PolskiDateParser
from ..przedmiot import Przedmioty

STYLE_DATY: dict[str, Callable[[datetime], str]] = {
    "Zwykły tekst (domyślny)": lambda d: f"\n{PolskiDateParser.WEEKDAYS[d.weekday()][1].capitalize()}, "
                                         f"{d.day} {PolskiDateParser.MONTHS[d.month - 1][1]}"
                                         f"{f' {rok}' if (rok := d.year) != date.today().year else ''}:\n",
    "Formatowanie Discorda": lambda d: f"\n<t:{d.timestamp()}:D>:\n",
    "Data i dzień tygodnia": lambda d: f"\n<t:{d.timestamp()}:F>:\n",
    "Krótka data": lambda d: f"\n<t:{d.timestamp()}:d>:\n",
    "Relatywnie": lambda d: f"\n<t:{d.timestamp()}:R>:\n",
    "Nie wyświetlaj daty": lambda d: ""
}

STYLE_CZASU: dict[str, Callable[[datetime], str]] = {
    "Zwykły tekst (domyślny)": lambda d: f' *({d.hour}:{d.minute:02})* ',
    "Formatowanie Discorda": lambda d: f' (<t:{d.timestamp()}:t>)',
    "Nie wyświetlaj czasu": lambda d: ""
}

STYLE_EMOJI: dict[str, Callable[[Przedmioty], str]] = {
    "Zwykłe (domyślne)": lambda p: p.emoji[0],
    "Losowe": lambda p: random.choice(p.emoji),
    "Nie wyświetlaj": lambda p: ""
}

STYLE_OPRACOWANIA: list[str] = [
    "Pod spisem (domyślnie)",
    "Przy każdym zadaniu",
    "Przy każdym zadaniu (z datą utworzenia)",
    "Nie wyświetlaj opracowania"
]
