from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from functools import cache
from typing import cast, Iterable, Any

import discord
from dateutil import parser
from discord import commands  # uwaga, zwykłe commands, nie discord.ext.commands
from discord.ext import tasks


# ------------------------- STAŁE

# Format: ID roli, ID serwera
EDYTOR = 931891996577103892, 885830592665628702
DEV = 938146467749707826, 885830592665628702

# ------------------------- STRUKTURY DANYCH


class PolskiDateParser(parser.parserinfo):
    """Klasa rozszerzająca parserinfo z dateutil.
    Pozwala ona na wprowadzanie dat w polskim formacie."""

    MONTHS = [
        ('sty', 'stycznia', 'styczeń', 'styczen', 'I'),
        ('lut', 'lutego', 'luty', 'II'),
        ('mar', 'marca', 'marzec', 'III'),
        ('kwi', 'kwietnia', 'kwiecień', 'kwiecien', 'IV'),
        ('maj', 'maja', 'V'),
        ('cze', 'czerwca', 'czerwiec', 'VI'),
        ('lip', 'lipca', 'lipiec', 'VII'),
        ('sie', 'sierpnia', 'sierpień', 'sierpien', 'VIII'),
        ('wrz', 'września', 'wrzesnia', 'wrzesień', 'wrzesien', 'IX'),
        ('paź', 'października', 'paz', 'pazdziernika', 'październik', 'pazdziernik', 'X'),
        ('lis', 'listopada', 'listopad', 'XI'),
        ('gru', 'grudnia', 'grudzień', 'grudzien', 'XII')
    ]

    WEEKDAYS = [
        ('pn', 'poniedziałek', 'poniedzialek', 'pon', 'po'),
        ('wt', 'wtorek', 'wto'),
        ('śr', 'środa', 'sr', 'sroda', 'śro', 'sro'),
        ('cz', 'czwartek', 'czw'),
        ('pt', 'piątek', 'piatek', 'pią', 'pia', 'pi'),
        ('sb', 'sobota', 'sob', 'so'),
        ('nd', 'niedziela', 'nie', 'ni', 'ndz')
    ]

    def __init__(self):
        super().__init__(True, False)


class Przedmioty(Enum):
    """Enumeracja wszystkich przedmiotów szkolnych.
    Pierwszy string w wartości danego przedmiotu jest jego nazwą, drugi - ogólnodostępnym emoji (np. flagą),
    a pozostałe - customowymi emoji, np. z twarzą nauczyciela."""

    ANGIELSKI = "Język angielski", "🇬🇧"
    POLSKI = "Język polski", "🇵🇱"
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
    def lista(cls) -> dict[str, Any]:  # Any, bo Przedmioty jeszcze nie są zadeklarowane
        """Zwraca dict listy nazw (key) i przedmiotów o tej nazwie (value)"""
        return {cast(str, p.nazwa): p for p in cls}


@dataclass(order=True, unsafe_hash=True)
class ZadanieDomowe:
    """Reprezentuje jedno zadanie domowe"""

    termin: datetime
    przedmiot: Przedmioty
    tresc: str
    task: tasks.Loop = field(hash=False, compare=False, repr=False)

    def stworz_task(self) -> tasks.Loop:
        """Tworzy task, którego celem jest usunięcie danego zadania domowego po upłynięciu jego terminu"""

        termin = (self.termin - datetime.now()).total_seconds()

        # Jeśli nie podano godziny przy tworzeniu zadania, usuń je dopiero o godzinie 23:59:30 danego dnia
        if self.termin.hour == 0 and self.termin.minute == 0:
            termin += 86370  # 23*60*60+59*60+30

        # Wykonaj 2 razy, raz po utworzeniu, raz po upłynięciu czasu
        @tasks.loop(seconds=termin, count=2)
        async def usun_zadanie_po_terminie():
            pass

        # Usuń zadanie dopiero po prawdziwym upłynięciu czasu
        @usun_zadanie_po_terminie.after_loop
        async def usun_after_loop():
            lista_zadan.remove(self)

        usun_zadanie_po_terminie.start()  # Wystartuj task
        return usun_zadanie_po_terminie

    def __init__(self, termin, przedmiot, tresc):
        """Inicjalizuje zadanie domowe i tworzy task do jego usunięcia"""
        self.tresc = tresc
        self.termin = termin
        self.przedmiot = przedmiot
        self.task = self.stworz_task()

    @property
    @cache
    def id(self):
        """Zwraca ID zadania, generowane na podstawie hasha zamienionego na system szesnastkowy"""
        return hex(abs(hash(self)))[2:]


PDP_INSTANCE = PolskiDateParser()
bot = discord.Bot()
storage: discord.DMChannel  # Kanał do zapisywania/backupowania/wczytywania stanu spisu
lista_zadan: list[ZadanieDomowe] = []

# ------------------------- STYLE


def _sorted_spis() -> list[ZadanieDomowe]:
    """Skrót do sorted(lista_zadan), bo PyCharm twierdzi, że przekazuję zły typ danych..."""
    return sorted(cast(Iterable, lista_zadan))


def oryginalny(dev: bool) -> dict[str, Any]:
    """Oryginalny styl spisu jeszcze sprzed istnienia tego bota (domyślne)"""

    wiadomosc = ""
    dzien = date.today() - timedelta(days=1)  # Wczoraj
    for zadanie in _sorted_spis():
        # Wyświetlanie dni
        if (data_zadania := zadanie.termin.date()) > dzien:
            wiadomosc += f"\n{PDP_INSTANCE.WEEKDAYS[data_zadania.weekday()][1].capitalize()}, " \
                         f"{data_zadania.day} {PDP_INSTANCE.MONTHS[data_zadania.month - 1][1]}:\n"
            dzien = data_zadania

        # Wypisywane tylko gdy czas był podany przy tworzeniu zadania
        czas = f' *(do {zadanie.termin.hour}:{zadanie.termin.minute:02})* ' \
            if not (zadanie.termin.hour == 0 and zadanie.termin.minute == 0) else ""
        # Jeśli zostały włączone "statystyki dla nerdów"
        dodatkowe = f" [ID: {zadanie.id}]" if dev else ""
        emoji = zadanie.przedmiot.emoji[0]

        wiadomosc += f"{emoji}**{zadanie.przedmiot.nazwa}**{emoji}{dodatkowe}:{czas} {zadanie.tresc}\n"

    return {"content": wiadomosc.strip()}


def pythonowe_repr(dev: bool) -> dict[str, Any]:
    """Lista wywołań Pythonowego repr() na każdym zadaniu domowym"""
    return {"content": "\n".join([(f'{zadanie.id}: ' if dev else '') + repr(zadanie) for zadanie in _sorted_spis()])}

# ------------------------- KOMENDY


@bot.slash_command(guild_ids=[EDYTOR[1]], default_permission=False)
@discord.commands.permissions.has_role(*EDYTOR)
async def dodaj_zadanie(
        ctx: commands.ApplicationContext,
        opis: commands.Option(str, "Treść zadania domowego"),
        termin: commands.Option(
            str,
            "Termin zadania domowego, np.: 'poniedziałek', 'pt 23:59', '21 III 2022'"
        ),
        przedmiot: commands.Option(
            str,
            "Przedmiot szkolny, z którego zadane jest zadanie",
            choices=Przedmioty.lista().keys(),
            default=Przedmioty.INNY.nazwa
        )
):
    """Dodaje nowe zadanie do spisu"""

    try:
        data = parser.parse(termin, PDP_INSTANCE)  # Konwertuje datę/godzinę podaną przez użytkownika na datetime
        if data < datetime.now():
            await ctx.respond("Zadanie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
            return
    except (parser.ParserError, ValueError):
        await ctx.respond("Wystąpił błąd przy konwersji daty!")
        return

    # Tworzy obiekt zadania i dodaje do spisu
    nowe_zadanie = ZadanieDomowe(data, Przedmioty.lista()[przedmiot], opis)
    lista_zadan.append(nowe_zadanie)
    await ctx.respond(f"Dodano nowe zadanie!\nID: {nowe_zadanie.id}")


@bot.slash_command(guild_ids=[EDYTOR[1]], default_permission=False)
@discord.commands.permissions.has_role(*EDYTOR)
async def usun_zadanie(
        ctx: commands.ApplicationContext,
        id_zadania: commands.Option(str, "ID zadania do usunięcia")
):
    """Usuwa zadanie o podanym ID ze spisu"""

    id_zadania = id_zadania.lower()
    znaleziono = None
    for zadanie in lista_zadan:
        if zadanie.id == id_zadania:
            znaleziono = zadanie
            break

    if not znaleziono:
        await ctx.respond("Nie znaleziono zadania o podanym ID!")
        return

    znaleziono.task.cancel()
    lista_zadan.remove(znaleziono)
    await ctx.respond("Usunięto zadanie!")


@bot.slash_command()
async def spis(
        ctx: commands.ApplicationContext,
        dodatkowe_opcje: commands.Option(
            str,
            "Pozwala na włączenie dodatkowej opcji formatowania lub wysłania wiadomości",
            choices=["Statystyki dla nerdów", "Wyślij wiadomość jako widoczną dla wszystkich", "Brak"],
            default="Brak"
        )
):
    """Wyświetla aktualny stan spisu"""

    styl = oryginalny
    wynik = styl(dodatkowe_opcje == "Statystyki dla nerdów")
    if len(wynik) == 1 and "content" in wynik and not wynik["content"]:
        await ctx.respond("Spis jest aktualnie pusty!",
                          ephemeral=(dodatkowe_opcje != "Wyślij wiadomość jako widoczną dla wszystkich"))
    else:
        await ctx.respond(ephemeral=(dodatkowe_opcje != "Wyślij wiadomość jako widoczną dla wszystkich"), **wynik)

# ------------------------- START BOTA


@bot.event
async def on_ready():
    """Wykonywane przy starcie bota"""

    global storage
    print(f"Zalogowano jako {bot.user}!")

    # Inicjalizacja kanału przechowywania backupu
    owner = (await bot.application_info()).owner
    storage = owner.dm_channel or await owner.create_dm()


def main(token: str):
    """Startuje bota zajmującego się spisem zadań domowych"""
    bot.run(token)


if __name__ == '__main__':
    from sys import argv
    from os import environ
    # Token jest wczytywany ze zmiennej środowiskowej lub pierwszego argumentu podanego przy uruchamianiu
    main(environ.get("SpisToken") or argv[1])
