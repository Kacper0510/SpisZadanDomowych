from functools import cache
from typing import Union, cast, Iterable
import discord
from discord import commands  # uwaga, zwykłe commands, nie discord.ext.commands
from discord.ext import tasks
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, date, timedelta
from dateutil import parser

# python310 -m pip install git+https://github.com/Pycord-Development/pycord.git@2d204e2b0e20e9420c89b037d74e3493cc1b2981
# https://discord.com/api/oauth2/authorize?client_id=931867818599780402&permissions=285615713344&scope=applications.commands%20bot

EDYTOR_SERWER = 885830592665628702
EDYTOR_ROLA = 931891996577103892

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
    INNY = "?", "❓"

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
    def lista(cls) -> tuple[str]:
        """Zwraca listę nazw przedmiotów, przekonwertowaną na małe litery"""
        return tuple(str(p.name).lower() for p in cls)


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


def oryginalny(dev: bool) -> Union[str, discord.Embed]:
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

    return wiadomosc.strip()


def pythonowe_repr(dev: bool) -> Union[str, discord.Embed]:
    """Lista wywołań Pythonowego repr() na każdym zadaniu domowym"""
    return "\n".join([(f'{zadanie.id}: ' if dev else '') + repr(zadanie) for zadanie in _sorted_spis()])

# ------------------------- KOMENDY


@bot.slash_command(guild_ids=[EDYTOR_SERWER], default_permission=False)
@discord.commands.permissions.has_role(EDYTOR_ROLA, EDYTOR_SERWER)
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
            choices=Przedmioty.lista(),
            default=Przedmioty.INNY.name.lower()
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

    nowe_zadanie = ZadanieDomowe(data, Przedmioty[przedmiot.upper()], opis)  # Tworzy obiekt zadania i dodaje do spisu
    lista_zadan.append(nowe_zadanie)
    await ctx.respond(f"Dodano nowe zadanie!\nID: {nowe_zadanie.id}")


@bot.slash_command(guild_ids=[EDYTOR_SERWER], default_permission=False)
@discord.commands.permissions.has_role(EDYTOR_ROLA, EDYTOR_SERWER)
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
        statystyki_dla_nerdow: commands.Option(bool, "Czy chcesz wyświetlić informacje typu ID zadania?", default=False)
):
    """Wyświetla aktualny stan spisu"""

    styl = oryginalny
    wynik = styl(statystyki_dla_nerdow)
    if type(wynik) == str:
        await ctx.respond(wynik, ephemeral=True)
    else:
        await ctx.respond("", embed=wynik, ephemeral=True)

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
    main(argv[1])  # Token jest wczytywany z pierwszego argumentu podanego przy uruchamianiu
