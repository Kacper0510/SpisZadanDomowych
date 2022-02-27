import logging
import pickle
import random
import re
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from functools import cache, total_ordering
from io import BytesIO
from os import getenv
from sys import stdout
from typing import cast, Any, List, Callable

import aiohttp  # Pycord i tak to importuje, nie trzeba dodawać do requirements
import discord
from dateutil.parser import parserinfo, ParserError, parser
from dateutil.relativedelta import relativedelta
from discord import commands  # Uwaga, zwykłe commands, nie discord.ext.commands
from discord.ext import tasks
from sortedcontainers import SortedList

# ------------------------- LOGGING

logger = logging.getLogger("spis")
LOGGER_FORMAT_DATY = "%d.%m.%y %H:%M:%S"
logging.basicConfig(
    level=getenv("Spis_LogLevel", "INFO").upper(),  # Poziom logowania
    style="{",
    format="[{asctime} {levelname} {name}/{funcName}] {message}",  # Format logów
    datefmt=LOGGER_FORMAT_DATY,  # Format daty
    stream=stdout  # Miejsce logowania: standardowe wyjście
)

# ------------------------- STAŁE


def _wczytaj_role_z_env(nazwa: str):
    """Wczytuje dane o roli z os.environ.
    Format: <id_roli>:<id_serwera>"""
    try:
        s = getenv(f"Spis_{nazwa}")
        if not s:
            logger.warning(f"Nie ustawiono zmiennej środowiskowej Spis_{nazwa}! Takie zachowanie nie było testowane!")
            return None, None
        s = s.split(":")
        ret = tuple(map(int, s))
        logger.debug(f"Wczytano zmienną środowiskową Spis_{nazwa}: {ret}")
        return ret
    except IndexError:
        logger.warning(f"Zmienną środowiskową Spis_{nazwa} podano w złym formacie!")
        return None, None


EDYTOR = _wczytaj_role_z_env("Edytor")
DEV = _wczytaj_role_z_env("Dev")

# Regex do znajdowania wszystkich linków w treści zadania
LINK_REGEX = re.compile(r"(https?://[a-zA-Z0-9-._~:/?#\[\]@!$&'()*+,;=%]*[a-zA-Z0-9-_~:/?#\[\]@!$&'()*+;=%])")
# Link do API GitHuba, aby zdobyć informacje o najnowszych zmianach
LINK_GITHUB_API = "https://api.github.com/repos/Kacper0510/SpisZadanDomowych/commits?per_page=1"
OSTATNI_COMMIT: dict | None = None


async def pobierz_informacje_z_githuba() -> None:
    """Pobiera informacje o ostatnich zmianach z GitHuba i zapisuje je do zmiennej OSTATNI_COMMIT"""
    global OSTATNI_COMMIT
    try:
        async with aiohttp.ClientSession() as session, session.get(LINK_GITHUB_API) as response:
            dane = (await response.json())[0]
        logger.info(f"Wczytano informacje z GitHuba: {dane['sha']}")

        # Ładne sformatowanie wczytanych informacji
        OSTATNI_COMMIT = \
            f"<t:{int(datetime.strptime(dane['commit']['author']['date'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}:R> " \
            f"- `{dane['sha'][:7]}` - [" + dane['commit']['message'].split('\n')[0] + f"]({dane['html_url']})"
    except aiohttp.ClientError as e:
        logger.exception(f"Nie udało się wczytać informacji z GitHuba!", exc_info=e)


# ------------------------- STRUKTURY DANYCH


class PolskiDateParser(parserinfo, parser):
    """Klasa rozszerzająca parser i przy okazji parserinfo z dateutil.
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
        parserinfo.__init__(self, True, False)  # Poprawne ustawienie formatu DD.MM.RR
        parser.__init__(self, self)  # Ustawienie parserinfo na self

    # noinspection PyMethodMayBeStatic
    def _build_naive(self, res, default: datetime) -> tuple[datetime, datetime]:
        """Nadpisane, aby naprawić problem z datami w przeszłości.
        Teraz zwraca tuple dwóch dat, zgodnie z opisem w docstringu parse()."""
        logging.debug(f"Parsowanie daty - surowe dane: {res}")
        replacement = {}
        for attr in ("year", "month", "day", "hour", "minute", "second", "microsecond"):
            if (v := getattr(res, attr)) is not None:  # Note to self: nie zapominać o nawiasie w walrusie
                replacement[attr] = v

        default = default.replace(**replacement)
        now = datetime.now()

        if res.weekday is not None:
            if res.day is None:
                default += timedelta(days=1)  # Nie pozwalamy na zwrócenie dzisiaj
            # Znajduje następny oczekiwany przez użytkownika dzień tygodnia
            default += timedelta(days=(res.weekday + 7 - default.weekday()) % 7)

        if default < now:  # Naprawa błędu z datą w przeszłości zamiast z najbliższą datą
            if res.hour is not None and res.day is None and res.weekday is None:
                default += timedelta(days=1)
            elif res.day is not None and res.month is None:
                default += relativedelta(months=1)
            elif res.month is not None and res.year is None:
                default += relativedelta(years=1)

        # Data usunięcia przesunięta odpowiednio do przodu od daty podanej przez użytkownika, zgodnie z sugestiami KK
        data_usuniecia = default
        # Przesuń godzinę do przodu o 45 min, chyba że użytkownik naprawdę wie, co robi (podał dużą dokładność)
        if res.second is None and res.microsecond is None:
            data_usuniecia += timedelta(minutes=45)
            # Przesuń godzinę na 16:00, jeśli użytkownik nie podał w ogóle godziny
            if res.hour is None and res.minute is None:
                data_usuniecia += timedelta(hours=15, minutes=15)  # 15:15 + 45 min = 16:00

        logging.debug(f"Parsowanie daty - wynik: {default}, {data_usuniecia}")
        return default, data_usuniecia

    # noinspection PyUnresolvedReferences
    def parse(self, timestr, default=None, ignoretz=False, tzinfos=None, **kwargs) -> tuple[datetime, datetime]:
        """Nadpisanie parser.parse - zwraca dwie daty zamiast jednej.
        Pierwszy datetime to prawdziwa data podana przez użytkownika, a drugi - zmodyfikowana data usunięcia zadania."""

        # Kod skopiowany w większości z oryginalnej implementacji
        if default is None:
            default = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        res = self._parse(timestr, **kwargs)[0]  # Ignorujemy resztę zwracanego tuple
        if res is None:
            raise ParserError("Unknown string format: %s", timestr)
        if len(res) == 0:
            raise ParserError("String does not contain a date: %s", timestr)
        try:
            p, m = self._build_naive(res, default)
        except ValueError as e:
            raise ParserError(str(e) + ": %s", timestr) from e
        if not ignoretz:
            p, m = self._build_tzaware(p, res, tzinfos), self._build_tzaware(m, res, tzinfos)
        return p, m


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


@total_ordering
@dataclass(eq=False, unsafe_hash=True)
class Ogloszenie:
    """Reprezentuje ogłoszenie wyświetlające się pod spisem"""

    termin_usuniecia: datetime
    tresc: str
    utworzono: tuple[int, datetime]  # Zawiera ID autora i datę utworzenia
    id: str = field(init=False, hash=False)
    task: tasks.Loop = field(init=False, hash=False, repr=False)

    @staticmethod
    def popraw_linki(tekst: str) -> str:
        """Poprawia podany tekst tak, aby linki nie generowały poglądów przy wypisywaniu spisu.
        Zasada działania: gdy link znajduje się w nawiasach ostrokątnych, nie generuje on embedów."""
        # \1 oznacza backtracking do 1 grupy każdego matcha, czyli do całego linku
        ret = LINK_REGEX.sub(r"<\1>", tekst)
        logger.debug(f'Poprawianie linków: {repr(tekst)} na {repr(ret)}')
        return ret

    def stworz_task(self):
        """Tworzy task, którego celem jest usunięcie danego zadania domowego po upłynięciu jego terminu"""

        termin = (self.termin_usuniecia - datetime.now()).total_seconds()

        # Wykonaj 2 razy, raz po utworzeniu, raz po upłynięciu czasu
        @tasks.loop(seconds=termin, count=2)
        async def usun_zadanie_po_terminie():
            if self.termin_usuniecia < datetime.now():  # Upewnij się, że to już czas
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


STYLE_DATY: dict[str, Callable[[datetime], str]] = {
    "Zwykły tekst (domyślny)": lambda d: f"\n{PDP.WEEKDAYS[d.weekday()][1].capitalize()}, "
                                         f"{d.day} {PDP.MONTHS[d.month - 1][1]}"
                                         f"{f' {rok}' if (rok := d.year) != date.today().year else ''}:\n",
    "Formatowanie Discorda": lambda d: f"\n<t:{d.timestamp()}:D>\n",
    "Data i dzień tygodnia": lambda d: f"\n<t:{d.timestamp()}:F>\n",
    "Krótka data": lambda d: f"\n<t:{d.timestamp()}:d>\n",
    "Relatywnie": lambda d: f"\n<t:{d.timestamp()}:R>\n",
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


@dataclass
class Styl:
    """Przechowuje ustawienia stylu wyświetlania spisu dla danego użytkownika"""

    embed: bool = False  # Wyświetlanie w embedzie zamiast w zwykłym tekście
    data: str = next(iter(STYLE_DATY))  # Sposób wyświetlania dat
    czas: str = next(iter(STYLE_CZASU))  # Sposób wyświetlania godziny zadania
    id: bool = False  # Wyświetlanie ID
    nazwa_przedmiotu: bool = True  # Wyświetlanie nazwy przedmiotu
    emoji: str = next(iter(STYLE_EMOJI))  # Sposób wyświetlania emoji przy przedmiocie
    opracowanie: str = STYLE_OPRACOWANIA[0]  # Sposób wyświetlania opracowania


@dataclass
class StanBota:
    """Klasa przechowująca stan bota między uruchomieniami"""

    lista_zadan: SortedList[Ogloszenie] = field(default_factory=SortedList)
    ostatni_zapis: datetime = field(default_factory=datetime.now)
    uzycia_spis: int = 0  # Globalna ilość użyć /spis
    style: dict[int, Styl] = field(default_factory=dict)  # Styl każdego użytkownika

    def __hash__(self):
        """Zwraca hash stanu"""
        dane_do_hashowania: tuple = (
            tuple(self.lista_zadan),
            self.ostatni_zapis,
            self.uzycia_spis,
            frozenset(self.style.items())
        )
        return hash(dane_do_hashowania)


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
        self.hash_stanu: int = 0  # Hash stanu bota przy ostatnim zapisie/wczytaniu
        self.autosave: bool = True  # Auto-zapis przy wyłączaniu i auto-wczytywanie przy włączaniu
        self.czas_startu = datetime.now()  # Czas startu bota, do obliczania uptime
        self.invite_link: str = ""  # Link do zaproszenia bota na serwer

    async def zapisz(self) -> bool:
        """Zapisuje stan bota do pliku i wysyła go do twórcy bota.
        Uwaga: zapis nie odbędzie się w przypadku wykrycia identycznego hasha stanu."""
        if hash(self.stan) == self.hash_stanu:  # Nic się nie zmieniło od ostatniego zapisu
            logger.info("Zapis stanu nie był konieczny - identyczny hash")
            return False

        ostatni_zapis_old = self.stan.ostatni_zapis  # Do przywrócenia w przypadku niepowodzenia zapisu
        self.stan.ostatni_zapis = datetime.now()
        try:
            backup = pickle.dumps(self.stan, pickle.HIGHEST_PROTOCOL)
            plik = discord.File(BytesIO(backup), f"spis_backup_{round(self.stan.ostatni_zapis.timestamp())}.pickle")
            await self.backup_kanal.send("", file=plik)
            logger.info(f"Pomyślnie zapisano plik {plik.filename} na kanale {repr(self.backup_kanal)}")
            logger.debug(f"Zapisane dane: {repr(self.stan)}")
            return True
        except pickle.PickleError as e:
            logger.exception("Nie udało się zapisać stanu jako obiekt pickle!", exc_info=e)
            self.stan.ostatni_zapis = ostatni_zapis_old
            return False
        finally:  # Zawsze przekalkuluj hash stanu
            self.hash_stanu = hash(self.stan)

    async def wczytaj(self) -> bool:
        """Wczytuje stan bota z kanału prywatnego twórcy bota"""
        try:
            ostatnia_wiadomosc = (await self.backup_kanal.history(limit=1).flatten())[0]
            if len(ostatnia_wiadomosc.attachments) != 1:
                logger.warning(f"Ostatnia wiadomość na kanale {repr(self.backup_kanal)} miała złą ilość załączników, "
                               f"porzucono wczytywanie stanu!")
                return False
            dane = await ostatnia_wiadomosc.attachments[0].read()
            self.stan = pickle.loads(dane, fix_imports=False)

            # Usuń zadania z przeszłości
            for zadanie in list(self.stan.lista_zadan):
                if zadanie.termin_usuniecia < datetime.now():
                    self.stan.lista_zadan.remove(zadanie)

            logger.info(f"Pomyślnie wczytano backup z {self.stan.ostatni_zapis.strftime(LOGGER_FORMAT_DATY)} "
                        f"z kanału {repr(self.backup_kanal)}")
            logger.debug(f"Zapisane dane: {repr(self.stan)}")
            return True
        except (pickle.PickleError, IndexError) as e:
            logger.exception("Nie udało się wczytać pliku pickle!", exc_info=e)
            self.stan = StanBota()
            return False
        finally:  # Zawsze przekalkuluj hash stanu
            self.hash_stanu = hash(self.stan)

    async def on_ready(self):
        """Wykonywane przy starcie bota"""
        logger.info(f"Zalogowano jako {self.user}!")

        # Inicjalizacja kanału przechowywania backupu
        wlasciciel = (await self.application_info()).owner
        self.backup_kanal = wlasciciel.dm_channel or await wlasciciel.create_dm()
        if self.autosave:
            await self.wczytaj()  # Próba wczytania
        else:
            self.stan = StanBota()

        self.invite_link = f"https://discord.com/api/oauth2/authorize?client_id={self.application_id}" \
                           f"&permissions=277025672192&scope=bot%20applications.commands"
        await pobierz_informacje_z_githuba()

    # noinspection PyMethodMayBeStatic
    async def on_guild_join(self, guild):
        """Wywoływane, gdy bota dodano do serwera"""
        logger.info(f"Bot został dodany do serwera {repr(guild)}")

    async def close(self):
        """Zamyka bota zapisując jego stan"""
        if self.autosave:
            await self.zapisz()  # Próba zapisu
        await super().close()

# ------------------------- ZMIENNE GLOBALNE


PDP = PolskiDateParser()  # Globalna instancja klasy PolskiDateParser
bot = SpisBot(
    intents=discord.Intents(guilds=True, dm_messages=True),
    activity=discord.Activity(type=discord.ActivityType.watching, name="/spis")
)

# ------------------------- STYLE


# Style i tak będą przepisane
def oryginalny(dev: bool) -> dict[str, Any]:
    """Oryginalny styl spisu jeszcze sprzed istnienia tego bota (domyślne)"""

    wiadomosc = ""
    dzien = date.today() - timedelta(days=1)  # Wczoraj
    for zadanie in bot.stan.lista_zadan:
        # Wyświetlanie dni
        if (data_zadania := zadanie.prawdziwy_termin.date()) > dzien:
            wiadomosc += f"\n{PDP.WEEKDAYS[data_zadania.weekday()][1].capitalize()}, " \
                         f"{data_zadania.day} {PDP.MONTHS[data_zadania.month - 1][1]}" \
                         f"{f' {rok}' if (rok := data_zadania.year) != date.today().year else ''}:\n"
            dzien = data_zadania

        # Wypisywane tylko gdy czas był podany przy tworzeniu zadania
        czas = f' *(do {zadanie.prawdziwy_termin.hour}:{zadanie.prawdziwy_termin.minute:02})* ' \
            if not (zadanie.prawdziwy_termin.hour == 0 and zadanie.prawdziwy_termin.minute == 0) else ""
        # Jeśli zostały włączone "statystyki dla nerdów"
        dodatkowe = f" [ID: {zadanie.id}]" if dev else ""
        emoji = zadanie.przedmiot.emoji[0]

        wiadomosc += f"{emoji}**{zadanie.przedmiot.nazwa}**{emoji}{dodatkowe}:{czas} {zadanie.tresc}\n"

    return {"content": wiadomosc.strip()}


def pythonowe_repr(_dev: bool) -> dict[str, Any]:
    """Lista wywołań Pythonowego repr() na każdym zadaniu domowym"""
    return {"content": "\n".join(
        [repr(zadanie) for zadanie in bot.stan.lista_zadan]
    )[:1990]}

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

    if len(opis) > 400:
        await ctx.respond("Za długa treść zadania!\nLimit znaków: 400")
        return
    try:
        data_p, data_u = PDP.parse(termin)  # Konwertuje datę/godzinę podaną przez użytkownika na dwa datetime'y
        if data_p < datetime.now():
            logger.debug(f'Użytkownik {repr(ctx.author)} podał datę z przeszłości: '
                         f'{repr(termin)} -> {data_p.strftime(LOGGER_FORMAT_DATY)}')
            await ctx.respond("Zadanie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
            return
    except (ParserError, ValueError) as e:
        logger.debug(f'Użytkownik {repr(ctx.author)} podał datę w niepoprawnym formacie: {repr(termin)}', exc_info=e)
        await ctx.respond("Wystąpił błąd przy konwersji daty!")
        return

    # Tworzy obiekt zadania i dodaje do spisu
    nowe_zadanie = ZadanieDomowe(data_u, opis, (ctx.author.id, datetime.now()), Przedmioty.lista()[przedmiot], data_p)
    bot.stan.lista_zadan.add(nowe_zadanie)
    logger.info(f"Dodano nowe zadanie: {repr(nowe_zadanie)}")
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
        logger.debug(f'Użytkownik {repr(ctx.author)} chciał usunąć nieistniejące zadanie o ID {repr(id_zadania)}')
        await ctx.respond("Nie znaleziono zadania o podanym ID!")
        return

    znaleziono.task.cancel()
    bot.stan.lista_zadan.remove(znaleziono)
    logger.info(f'Użytkownik {repr(ctx.author)} usunął zadanie: {repr(znaleziono)}')
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
    bot.stan.uzycia_spis += 1
    logger.debug(f"Użytkownik {repr(ctx.author)} wyświetlił spis{f' ({dodatkowe_opcje})' if dodatkowe_opcje else ''}")


@bot.slash_command()
async def info(ctx: commands.ApplicationContext):
    """Wyświetla statystyki i informacje o bocie"""
    # Kolor przewodni wywołującego komendę
    kolor_uzytkownika = (await bot.fetch_user(ctx.author.id)).accent_color or discord.embeds.EmptyEmbed
    embed = discord.Embed(color=kolor_uzytkownika,
                          title="Informacje o bocie",
                          url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Rickroll, bo czemu nie XD
    embed.set_thumbnail(url=bot.user.avatar.url)  # Miniatura - profilowe bota

    # Pola embeda
    embed.add_field(name="Twórca bota", value=str(bot.backup_kanal.recipient), inline=False)

    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)} ms")
    uptime = str(datetime.now() - bot.czas_startu)
    if kropka := uptime.find("."):  # Pozbywamy się mikrosekund
        uptime = uptime[:kropka]
    embed.add_field(name="Czas pracy", value=uptime)
    embed.add_field(name="Serwery", value=len(bot.guilds))

    embed.add_field(name="Ostatni backup", value=f"<t:{round(bot.stan.ostatni_zapis.timestamp())}:R>")
    embed.add_field(name="Globalna ilość użyć `/spis`", value=bot.stan.uzycia_spis)

    if OSTATNI_COMMIT:
        embed.add_field(name="Ostatnia aktualizacja", value=OSTATNI_COMMIT, inline=False)

    # Przyciski pod wiadomością
    przyciski = discord.ui.View(
        discord.ui.Button(
            label="Dodaj na serwer",
            url=bot.invite_link,
            emoji="📲"
        ),
        discord.ui.Button(
            label="Kod źródłowy i informacje",
            url="https://github.com/Kacper0510/SpisZadanDomowych",
            emoji="⌨"
        ),
        timeout=None
    )

    await ctx.respond(embed=embed, ephemeral=True, view=przyciski)
    logger.debug(f"Użytkownik {repr(ctx.author)} wyświetlił informacje o bocie")


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


def main():
    """Startuje bota zajmującego się spisem zadań domowych, wczytując token z os.environ"""
    token = getenv("Spis_Token")
    if not token:
        logger.critical('Nie udało się odnaleźć tokena! Podaj go w zmiennej środowiskowej "Spis_Token"')
        return

    bot.autosave = getenv("Spis_Autosave", "t").lower() in ("true", "t", "yes", "y", "1", "on", "prawda", "p", "tak")
    logger.debug(f"Autosave: {bot.autosave}")
    bot.run(token)


if __name__ == '__main__':
    main()
