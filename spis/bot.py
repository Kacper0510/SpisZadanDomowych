import pickle
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from logging import getLogger

import aiohttp
import discord
from sortedcontainers import SortedList

from .style import Styl
from .zadanie import Ogloszenie

__all__ = "SpisBot", "PROSTY_FORMAT_DATY"
logger = getLogger(__name__)

# Link do API GitHuba, aby zdobyć informacje o najnowszych zmianach
LINK_GITHUB_API: str = "https://api.github.com/repos/Kacper0510/SpisZadanDomowych/commits?per_page=1"
PROSTY_FORMAT_DATY = "%d.%m.%y %H:%M:%S"


@dataclass
class StanBota:
    """Klasa przechowująca stan bota między uruchomieniami"""

    lista_zadan: SortedList[Ogloszenie] = field(default_factory=SortedList)
    style: dict[int, Styl] = field(default_factory=dict)  # Styl każdego użytkownika

    ostatni_zapis: datetime = field(default_factory=datetime.now)
    uzycia_spis: int = 0  # Globalna ilość użyć /spis
    edytor: int | None = None  # ID serwera, na którym można edytować spis

    def __hash__(self):
        """Zwraca hash stanu"""
        dane_do_hashowania: tuple = (
            tuple(self.lista_zadan),
            frozenset(self.style.items()),
            self.ostatni_zapis,
            self.uzycia_spis,
            self.edytor
        )
        return hash(dane_do_hashowania)


class SpisBot(discord.Bot):
    """Rozszerzenie podstawowego bota o potrzebne metody"""

    def __init__(self, *args, **kwargs):
        """Inicjalizacja zmiennych"""
        super().__init__(*args, **kwargs)

        self.stan: StanBota | None = None

        # Konfiguracja
        self.autosave: bool = True  # Auto-zapis przy wyłączaniu i auto-wczytywanie przy włączaniu
        self.serwer_dev: int | None = None  # Serwer do zarejestrowania komend developerskich

        # Dane uzupełniane przy inicjalizacji
        self.backup_kanal: discord.DMChannel | None = None  # Kanał do zapisywania/backupowania/wczytywania stanu spisu
        self.hash_stanu: int = 0  # Hash stanu bota przy ostatnim zapisie/wczytaniu
        self.czas_startu = datetime.now()  # Czas startu bota, do obliczania uptime
        self.invite_link: str = ""  # Link do zaproszenia bota na serwer
        self.ostatni_commit: str = ""  # Ostatnia aktualizacja bota

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

            logger.info(f"Pomyślnie wczytano backup z {self.stan.ostatni_zapis.strftime(PROSTY_FORMAT_DATY)} "
                        f"z kanału {repr(self.backup_kanal)}")
            logger.debug(f"Zapisane dane: {repr(self.stan)}")
            return True
        except (pickle.PickleError, IndexError) as e:
            logger.exception("Nie udało się wczytać pliku pickle!", exc_info=e)
            self.stan = StanBota()
            return False
        finally:  # Zawsze przekalkuluj hash stanu
            self.hash_stanu = hash(self.stan)

    async def _pobierz_informacje_z_githuba(self) -> None:
        """Pobiera informacje o ostatnich zmianach z GitHuba i zapisuje je do zmiennej OSTATNI_COMMIT"""
        try:
            async with aiohttp.ClientSession() as session, session.get(LINK_GITHUB_API) as response:
                dane = (await response.json())[0]
            logger.info(f"Wczytano informacje z GitHuba: {dane['sha']}")

            # Ładne sformatowanie wczytanych informacji
            self.ostatni_commit = \
                f"<t:{int(datetime.strptime(dane['commit']['author']['date'], '%Y-%m-%dT%H:%M:%S%z').timestamp())}:R> "\
                f"- `{dane['sha'][:7]}` - [" + dane['commit']['message'].split('\n')[0] + f"]({dane['html_url']})"
        except aiohttp.ClientError as e:
            logger.exception(f"Nie udało się wczytać informacji z GitHuba!", exc_info=e)

    async def on_connect(self):
        """Nadpisane, aby uniknąć zbędnego wywołania sync_commands()"""
        pass

    async def on_ready(self):
        """Wykonywane przy starcie bota"""
        logger.info(f"Zalogowano jako {self.user}!")

        # Inicjalizacja kanału przechowywania backupu
        wlasciciel = (await self.application_info()).owner
        self.owner_id = wlasciciel.id
        self.backup_kanal = wlasciciel.dm_channel or await wlasciciel.create_dm()
        if self.autosave:
            await self.wczytaj()  # Próba wczytania
        else:
            self.stan = StanBota()

        self.invite_link = f"https://discord.com/api/oauth2/authorize?client_id={self.application_id}" \
                           f"&permissions=277025672192&scope=bot%20applications.commands"
        await self._pobierz_informacje_z_githuba()

        # Ładowanie rozszerzeń zawierających komendy bota
        for ext in ("global", "dev", "edytor"):
            self.load_extension("spis.komendy." + ext)
        await self.sync_commands()

        logger.info("Wczytywanie zakończone!")

    # noinspection PyMethodMayBeStatic
    async def on_guild_join(self, guild):
        """Wywoływane, gdy bota dodano do serwera"""
        logger.info(f"Bot został dodany do serwera {repr(guild)}")

    async def close(self):
        """Zamyka bota zapisując jego stan"""
        if self.autosave:
            await self.zapisz()  # Próba zapisu
        await super().close()
