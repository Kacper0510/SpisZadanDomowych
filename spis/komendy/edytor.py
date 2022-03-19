from datetime import datetime
from logging import getLogger

from discord import commands, Cog

from ..bot import SpisBot, PROSTY_FORMAT_DATY
from ..date_parser import *
from ..przedmiot import Przedmioty
from ..zadanie import *

logger = getLogger(__name__)

LIMIT_ZNAKOW = 250  # Limit znaków w ogłoszeniu/zadaniu domowym
wlasciciel = [commands.CommandPermission("owner", 2, True)]


class KomendyDlaEdytorow(Cog):

    def __init__(self, bot: SpisBot):
        self.bot = bot
        if bot.stan.edytor is not None:
            for cmd in self.__cog_commands__:
                cmd.guild_ids = [bot.stan.edytor[1]]
                cmd.permissions.append(commands.CommandPermission(bot.stan.edytor[0], 1, True, bot.stan.edytor[1]))

    dodaj = commands.SlashCommandGroup("dodaj", "Komendy dodające ogłoszenia i zadania", permissions=wlasciciel)

    @dodaj.command()
    async def zadanie(
            self,
            ctx: commands.ApplicationContext,
            opis: commands.Option(str, "Treść zadania domowego"),
            termin: commands.Option(
                str,
                "Termin zadania domowego, np.: 'poniedziałek', 'pt 23:59', '21 III 2022'"
            ),
            przedmiot: commands.Option(
                str,
                "Przedmiot szkolny, z którego zadane jest zadanie",
                choices=Przedmioty.lista().keys()
            )
    ):
        """Dodaje nowe zadanie do spisu"""
        if len(opis) > LIMIT_ZNAKOW:
            await ctx.respond(f"Za długa treść zadania!\nLimit znaków: {LIMIT_ZNAKOW}")
            return
        try:
            # Konwertuje datę/godzinę podaną przez użytkownika na dwa datetime'y
            data_p, data_u = PolskiDateParser.parse(termin)
            if data_p < datetime.now():
                logger.debug(f'Użytkownik {repr(ctx.author)} podał datę z przeszłości: '
                             f'{repr(termin)} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                await ctx.respond("Zadanie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
                return
        except (ParserError, ValueError) as e:
            logger.debug(f'Użytkownik {repr(ctx.author)} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
            await ctx.respond("Wystąpił błąd przy konwersji daty!")
            return

        # Tworzy obiekt zadania i dodaje do spisu
        nowe_zadanie = ZadanieDomowe(data_u, opis, (ctx.author.id, datetime.now()),
                                     Przedmioty.lista()[przedmiot], data_p)
        self.bot.stan.lista_zadan.add(nowe_zadanie)
        logger.info(f"Dodano nowe zadanie: {repr(nowe_zadanie)}")
        await ctx.respond(f"Dodano nowe zadanie!\nID: {nowe_zadanie.id}")

    @dodaj.command()
    async def ogloszenie(
            self,
            ctx: commands.ApplicationContext,
            opis: commands.Option(str, "Treść ogłoszenia"),
            termin: commands.Option(
                str,
                "Termin usunięcia ogłoszenia, np.: 'poniedziałek', 'pt 23:59', '21 III 2022'"
            )
    ):
        """Dodaje nowe ogłoszenie do spisu"""
        if len(opis) > LIMIT_ZNAKOW:
            await ctx.respond(f"Za długa treść ogłoszenia!\nLimit znaków: {LIMIT_ZNAKOW}")
            return
        try:
            # Konwertuje datę/godzinę podaną przez użytkownika na dwa datetime'y
            data_p = PolskiDateParser.parse(termin)[0]
            if data_p < datetime.now():
                logger.debug(f'Użytkownik {repr(ctx.author)} podał datę z przeszłości: '
                             f'{repr(termin)} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                await ctx.respond("Ogłoszenie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
                return
        except (ParserError, ValueError) as e:
            logger.debug(f'Użytkownik {repr(ctx.author)} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
            await ctx.respond("Wystąpił błąd przy konwersji daty!")
            return

        # Tworzy obiekt zadania i dodaje do spisu
        nowe_ogloszenie = Ogloszenie(data_p, opis, (ctx.author.id, datetime.now()))
        self.bot.stan.lista_zadan.add(nowe_ogloszenie)
        logger.info(f"Dodano nowe ogłoszenie: {repr(nowe_ogloszenie)}")
        await ctx.respond(f"Dodano nowe ogłoszenie!\nID: {nowe_ogloszenie.id}")

    @commands.slash_command()
    async def usun(
            self,
            ctx: commands.ApplicationContext,
            id_zadania: commands.Option(str, "ID zadania/ogłoszenia do usunięcia")
    ):
        """Usuwa zadanie lub ogłoszenie o podanym ID ze spisu"""
        id_zadania = id_zadania.lower()
        znaleziono = None
        for zadanie in self.bot.stan.lista_zadan:
            if zadanie.id == id_zadania:
                znaleziono = zadanie
                break

        if not znaleziono:
            logger.debug(f'Użytkownik {repr(ctx.author)} chciał usunąć nieistniejące ID: {repr(id_zadania)}')
            await ctx.respond("Nie znaleziono zadania/ogłoszenia o podanym ID!")
            return

        znaleziono.task.cancel()
        self.bot.stan.lista_zadan.remove(znaleziono)
        logger.info(f'Użytkownik {repr(ctx.author)} usunął zadanie/ogłoszenie: {repr(znaleziono)}')
        await ctx.respond("Usunięto zadanie/ogłoszenie!")


def setup(bot: SpisBot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_cog(KomendyDlaEdytorow(bot))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
