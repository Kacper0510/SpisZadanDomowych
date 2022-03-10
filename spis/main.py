import logging
from os import getenv
from sys import stdout

from discord import Intents, Activity, ActivityType

__all__ = "PROSTY_FORMAT_DATY", "OSTATNI_COMMIT", "main", "bot"
logger = logging.getLogger("spis.main")

PROSTY_FORMAT_DATY = "%d.%m.%y %H:%M:%S"
OSTATNI_COMMIT: dict | None = None


def _konfiguruj_logging():
    logging.basicConfig(
        level=getenv("Spis_LogLevel", "INFO").upper(),  # Poziom logowania
        style="{",
        format="[{asctime} {levelname} {name}/{funcName}] {message}",  # Format logów
        datefmt=PROSTY_FORMAT_DATY,  # Format daty
        stream=stdout  # Miejsce logowania: standardowe wyjście
    )


bot = None


def main():
    """Startuje bota zajmującego się spisem zadań domowych, wczytując token z os.environ"""
    _konfiguruj_logging()

    token = getenv("Spis_Token")
    if not token:
        logger.critical('Nie udało się odnaleźć tokena! Podaj go w zmiennej środowiskowej "Spis_Token"')
        return

    global bot
    from .bot import SpisBot
    bot = SpisBot(
        intents=Intents(guilds=True, dm_messages=True),
        activity=Activity(type=ActivityType.watching, name="/spis")
    )

    bot.autosave = getenv("Spis_Autosave", "t").lower() in ("true", "t", "yes", "y", "1", "on", "prawda", "p", "tak")
    logger.debug(f"Autosave: {bot.autosave}")
    bot.run(token)
