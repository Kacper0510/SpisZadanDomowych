import pickle
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from functools import cache, total_ordering
from io import BytesIO
from typing import cast, Iterable, Any, List

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

        termin = (self.termin - datetime.now()).total_seconds() + 5  # 5 sekund później, just to be sure

        # Jeśli nie podano godziny przy tworzeniu zadania, usuń je dopiero o godzinie 23:59:30 danego dnia
        if self.termin.hour == 0 and self.termin.minute == 0:
            termin += 86370  # 23*60*60+59*60+30

        # Wykonaj 2 razy, raz po utworzeniu, raz po upłynięciu czasu
        @tasks.loop(seconds=termin, count=2)
        async def usun_zadanie_po_terminie():
            if self.termin < datetime.now():  # Upewnij się, że to już czas
                bot.stan.lista_zadan.remove(self)

        usun_zadanie_po_terminie.start()  # Wystartuj task
        return usun_zadanie_po_terminie

    def __init__(self, termin, przedmiot, tresc):
        """Inicjalizuje zadanie domowe i tworzy task do jego usunięcia"""
        self.tresc = tresc
        self.termin = termin
        self.przedmiot = przedmiot
        self.task = self.stworz_task()

    def __del__(self):
        """Przy destrukcji obiektu kończy też task"""
        self.task.cancel()

    def __getstate__(self) -> tuple:
        """Zapisuje w pickle wszystkie dane zadania domowego oprócz taska"""
        return self.termin, self.przedmiot, self.tresc

    def __setstate__(self, state: tuple):
        """Wczytuje stan obiektu z pickle"""
        self.termin, self.przedmiot, self.tresc = state
        self.task = self.stworz_task()

    @property
    @cache
    def id(self):
        """Zwraca ID zadania, generowane na podstawie hasha zamienionego na system szesnastkowy"""
        return hex(abs(hash(self)))[2:]


@dataclass
class StanBota:
    """Klasa przechowująca stan bota między uruchomieniami"""

    lista_zadan: list[ZadanieDomowe] = field(default_factory=list)


class SpisBot(discord.Bot):
    """Rozszerzenie podstawowego bota o potrzebne metody"""

    async def register_command(self, command: discord.ApplicationCommand, force: bool = True,
                               guild_ids: List[int] = None) -> None:
        """Musiałem to zaimplementować, bo nie chciało się tego zrobić twórcom pycorda..."""
        for guild in guild_ids:
            await self.register_commands([command], guild, force)

    def __init__(self, *args, **kwargs):
        """Inicjalizacja zmiennych"""
        super().__init__(*args, **kwargs)

        self.backup_kanal: discord.DMChannel | None = None  # Kanał do zapisywania/backupowania/wczytywania stanu spisu
        self.stan: StanBota | None = None

    async def zapisz(self) -> bool:
        """Zapisuje stan bota do pliku i wysyła go do twórcy bota"""
        try:
            backup = pickle.dumps(self.stan, pickle.HIGHEST_PROTOCOL)
            plik = discord.File(BytesIO(backup), f"spis_backup_{int(datetime.now().timestamp())}.pickle")
            await self.backup_kanal.send("", file=plik)
            return True
        except pickle.PickleError:
            print("Nie udało się zapisać obiektu jako pickle!")
            return False

    async def wczytaj(self) -> bool:
        """Wczytuje stan bota z kanału prywatnego twórcy bota"""
        try:
            ostatnia_wiadomosc = (await self.backup_kanal.history(limit=1).flatten())[0]
            if len(ostatnia_wiadomosc.attachments) != 1:
                return False
            dane = await ostatnia_wiadomosc.attachments[0].read()
            self.stan = pickle.loads(dane, fix_imports=False)

            # Usuń zadania z przeszłości
            for zadanie in list(self.stan.lista_zadan):
                if zadanie.termin < datetime.now():
                    self.stan.lista_zadan.remove(zadanie)

            return True
        except pickle.PickleError | IndexError:
            print("Nie udało się wczytać pliku pickle!")
            return False

    async def on_ready(self):
        """Wykonywane przy starcie bota"""
        print(f"Zalogowano jako {self.user}!")

        # Inicjalizacja kanału przechowywania backupu i próba wczytania
        wlasciciel = (await self.application_info()).owner
        self.backup_kanal = wlasciciel.dm_channel or await wlasciciel.create_dm()
        if await self.wczytaj():
            print("Pomyślnie wczytano backup!")
        else:
            self.stan = StanBota()  # Stwórz stan bota, jeśli nie istnieje

    async def close(self):
        """Zamyka bota zapisując jego stan"""
        print(f"Zapisanie stanu{'' if await self.zapisz() else ' nie'} powiodło się!")
        await super().close()

# ------------------------- ZMIENNE GLOBALNE


PDP_INSTANCE = PolskiDateParser()
bot = SpisBot()

# ------------------------- STYLE


def _sorted_spis() -> list[ZadanieDomowe]:
    """Skrót do sorted(lista_zadan), bo PyCharm twierdzi, że przekazuję zły typ danych..."""
    return sorted(cast(Iterable, bot.stan.lista_zadan))


def oryginalny(dev: bool) -> dict[str, Any]:
    """Oryginalny styl spisu jeszcze sprzed istnienia tego bota (domyślne)"""

    wiadomosc = ""
    dzien = date.today() - timedelta(days=1)  # Wczoraj
    for zadanie in _sorted_spis():
        # Wyświetlanie dni
        if (data_zadania := zadanie.termin.date()) > dzien:
            wiadomosc += f"\n{PDP_INSTANCE.WEEKDAYS[data_zadania.weekday()][1].capitalize()}, " \
                         f"{data_zadania.day} {PDP_INSTANCE.MONTHS[data_zadania.month - 1][1]}" \
                         f"{f' {rok}' if (rok := data_zadania.year) != date.today().year else ''}:\n"
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
    bot.stan.lista_zadan.append(nowe_zadanie)
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
    for zadanie in bot.stan.lista_zadan:
        if zadanie.id == id_zadania:
            znaleziono = zadanie
            break

    if not znaleziono:
        await ctx.respond("Nie znaleziono zadania o podanym ID!")
        return

    znaleziono.task.cancel()
    bot.stan.lista_zadan.remove(znaleziono)
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


@bot.slash_command(guild_ids=[DEV[1]], default_permission=False)
@discord.commands.permissions.has_role(*DEV)
async def zapisz_stan(ctx: commands.ApplicationContext):
    """Zapisuje stan bota do pliku i wysyła go do twórcy bota"""

    sukces = await bot.zapisz()
    await ctx.respond(f"Zapisanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)


@bot.slash_command(guild_ids=[DEV[1]], default_permission=False)
@discord.commands.permissions.has_role(*DEV)
async def wczytaj_stan(ctx: commands.ApplicationContext):
    """Wczytuje stan bota z kanału prywatnego twórcy bota (liczy się tylko ostatnia wiadomość)"""

    sukces = await bot.wczytaj()
    await ctx.respond(f"Wczytanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)

# ------------------------- START BOTA


def main(token: str):
    """Startuje bota zajmującego się spisem zadań domowych"""
    bot.run(token)


if __name__ == '__main__':
    from sys import argv
    from os import environ

    # Token jest wczytywany ze zmiennej środowiskowej lub pierwszego argumentu podanego przy uruchamianiu
    try:
        main(environ.get("SpisToken") or argv[1])
    except IndexError:
        print('Nie udało się odnaleźć tokena!\n'
              'Podaj go w argumencie do uruchomienia lub w zmiennej środowiskowej "SpisToken".')
