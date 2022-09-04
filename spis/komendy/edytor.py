from datetime import datetime
from logging import getLogger
from typing import cast

from discord import commands, Cog, utils

from ..bot import SpisBot, PROSTY_FORMAT_DATY
from ..date_parser import *
from ..przedmiot import Przedmioty
from ..style import DOMYSLNY_STYL
from ..zadanie import *

logger = getLogger(__name__)

LIMIT_ZNAKOW = 250  # Limit znaków w ogłoszeniu/zadaniu domowym


class KomendyDlaEdytorow(Cog):

    def __init__(self, bot: SpisBot):
        self.bot = bot
        if bot.stan.edytor is not None:
            for cmd in self.__cog_commands__:
                cmd.guild_ids = [bot.stan.edytor]

    dodaj = commands.SlashCommandGroup("dodaj", "Komendy dodające ogłoszenia i zadania")
    edytuj = commands.SlashCommandGroup("edytuj", "Komendy edytujące ogłoszenia i zadania")

    @dodaj.command(name="zadanie")
    async def dodaj_zadanie(
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
                logger.debug(f'Użytkownik {ctx.author!r} podał datę z przeszłości: '
                             f'{termin!r} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                await ctx.respond("Zadanie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
                return
        except (ParserError, ValueError) as e:
            logger.debug(f'Użytkownik {ctx.author!r} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
            await ctx.respond("Wystąpił błąd przy konwersji daty!")
            return

        # Tworzy obiekt zadania i dodaje do spisu
        nowe_zadanie = ZadanieDomowe(data_u, opis, (ctx.author.id, datetime.now()),
                                     Przedmioty.lista()[przedmiot], data_p)
        self.bot.stan.lista_zadan.add(nowe_zadanie)
        logger.info(f"Dodano nowe zadanie: {nowe_zadanie!r}")

        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        await ctx.respond(**styl.formatuj_zadanie("Dodano nowe zadanie!", nowe_zadanie, wymus_id=True))

    @dodaj.command(name="ogloszenie")
    async def dodaj_ogloszenie(
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
                logger.debug(f'Użytkownik {ctx.author!r} podał datę z przeszłości: '
                             f'{termin!r} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                await ctx.respond("Ogłoszenie nie zostało zarejestrowane, ponieważ podano datę z przeszłości!")
                return
        except (ParserError, ValueError) as e:
            logger.debug(f'Użytkownik {ctx.author!r} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
            await ctx.respond("Wystąpił błąd przy konwersji daty!")
            return

        # Tworzy obiekt zadania i dodaje do spisu
        nowe_ogloszenie = Ogloszenie(data_p, opis, (ctx.author.id, datetime.now()))
        self.bot.stan.lista_zadan.add(nowe_ogloszenie)
        logger.info(f"Dodano nowe ogłoszenie: {nowe_ogloszenie!r}")

        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        await ctx.respond(**styl.formatuj_ogloszenie("Dodano nowe ogłoszenie!", nowe_ogloszenie, wymus_id=True))

    @edytuj.command(name="zadanie")
    async def edytuj_zadanie(
            self,
            ctx: commands.ApplicationContext,
            id_do_edycji: commands.Option(str, "ID zadania/ogłoszenia do edycji"),
            opis: commands.Option(str, "Treść zadania domowego") = None,
            termin: commands.Option(
                str,
                "Termin zadania domowego, np.: 'poniedziałek', 'pt 23:59', '21 III 2022'"
            ) = None,
            przedmiot: commands.Option(
                str,
                "Przedmiot szkolny, z którego zadane jest zadanie",
                choices=Przedmioty.lista().keys()
            ) = None
    ):
        """Edytuje zadanie o podanym ID"""
        id_do_edycji = id_do_edycji.lower()
        znaleziono = utils.get(self.bot.stan.lista_zadan, id=id_do_edycji)

        if not znaleziono or type(znaleziono) != ZadanieDomowe:
            logger.debug(f'Użytkownik {ctx.author!r} chciał edytować nieistniejące zadanie: {id_do_edycji!r}')
            await ctx.respond("Nie znaleziono zadania o podanym ID!")
            return
        znaleziono = cast(ZadanieDomowe, znaleziono)

        zmiany = []
        if opis is not None:
            if len(opis) > LIMIT_ZNAKOW:
                await ctx.respond(f"Za długa treść zadania!\nLimit znaków: {LIMIT_ZNAKOW}")
                return
            zmiany.append("opis")
        data_p, data_u = None, None
        if termin is not None:
            try:
                # Konwertuje datę/godzinę podaną przez użytkownika na dwa datetime'y
                data_p, data_u = PolskiDateParser.parse(termin)
                if data_p < datetime.now():
                    logger.debug(f'Użytkownik {ctx.author!r} podał datę z przeszłości: '
                                 f'{termin!r} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                    await ctx.respond("Zadanie nie zostało zmienione, ponieważ podano datę z przeszłości!")
                    return
                zmiany.append("termin")
            except (ParserError, ValueError) as e:
                logger.debug(f'Użytkownik {ctx.author!r} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
                await ctx.respond("Wystąpił błąd przy konwersji daty!")
                return
        if przedmiot is not None:
            zmiany.append("przedmiot")

        if len(zmiany) == 0:
            logger.debug(f'Użytkownik {ctx.author!r} nic nie zmienił w zadaniu: {znaleziono!r}')
            await ctx.respond("Nic nie zostało zmienione!")
            return
        if "opis" in zmiany:
            znaleziono.tresc = znaleziono.popraw_linki(opis)
        if "termin" in zmiany:
            znaleziono.termin_usuniecia = data_u
            znaleziono.prawdziwy_termin = data_p
            znaleziono.task.cancel()
            znaleziono.stworz_task()
        if "przedmiot" in zmiany:
            znaleziono.przedmiot = Przedmioty.lista()[przedmiot]

        logger.info(f'Użytkownik {ctx.author!r} edytował zadanie: {znaleziono!r}')

        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        await ctx.respond(**styl.formatuj_zadanie("Edytowano zadanie!", znaleziono))

    @edytuj.command(name="ogloszenie")
    async def edytuj_ogloszenie(
            self,
            ctx: commands.ApplicationContext,
            id_do_edycji: commands.Option(str, "ID zadania/ogłoszenia do edycji"),
            opis: commands.Option(str, "Treść ogłoszenia") = None,
            termin: commands.Option(
                str,
                "Termin usunięcia ogłoszenia, np.: 'poniedziałek', 'pt 23:59', '21 III 2022'"
            ) = None
    ):
        """Edytuje ogłoszenie o podanym ID"""
        id_do_edycji = id_do_edycji.lower()
        znaleziono = utils.get(self.bot.stan.lista_zadan, id=id_do_edycji)

        if not znaleziono or type(znaleziono) == ZadanieDomowe:
            logger.debug(f'Użytkownik {ctx.author!r} chciał edytować nieistniejące ogłoszenie: {id_do_edycji!r}')
            await ctx.respond("Nie znaleziono ogłoszenia o podanym ID!")
            return

        zmiany = []
        if opis is not None:
            if len(opis) > LIMIT_ZNAKOW:
                await ctx.respond(f"Za długa treść ogłoszenia!\nLimit znaków: {LIMIT_ZNAKOW}")
                return
            zmiany.append("opis")
        data_p = None
        if termin is not None:
            try:
                # Konwertuje datę/godzinę podaną przez użytkownika na dwa datetime'y
                data_p = PolskiDateParser.parse(termin)[0]
                if data_p < datetime.now():
                    logger.debug(f'Użytkownik {ctx.author!r} podał datę z przeszłości: '
                                 f'{termin!r} -> {data_p.strftime(PROSTY_FORMAT_DATY)}')
                    await ctx.respond("Ogłoszenie nie zostało zmienione, ponieważ podano datę z przeszłości!")
                    return
                zmiany.append("termin")
            except (ParserError, ValueError) as e:
                logger.debug(f'Użytkownik {ctx.author!r} podał datę w niepoprawnym formacie: {termin!r}', exc_info=e)
                await ctx.respond("Wystąpił błąd przy konwersji daty!")
                return

        if len(zmiany) == 0:
            logger.debug(f'Użytkownik {ctx.author!r} nic nie zmienił w ogłoszeniu: {znaleziono!r}')
            await ctx.respond("Nic nie zostało zmienione!")
            return
        if "opis" in zmiany:
            znaleziono.tresc = znaleziono.popraw_linki(opis)
        if "termin" in zmiany:
            znaleziono.termin_usuniecia = data_p
            znaleziono.task.cancel()
            znaleziono.stworz_task()

        logger.info(f'Użytkownik {ctx.author!r} edytował ogłoszenie: {znaleziono!r}')

        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        await ctx.respond(**styl.formatuj_ogloszenie("Edytowano ogłoszenie!", znaleziono))

    @commands.slash_command()
    async def usun(
            self,
            ctx: commands.ApplicationContext,
            id_do_usuniecia: commands.Option(str, "ID zadania/ogłoszenia do usunięcia")
    ):
        """Usuwa zadanie lub ogłoszenie o podanym ID ze spisu"""
        id_do_usuniecia = id_do_usuniecia.lower()
        znaleziono = utils.get(self.bot.stan.lista_zadan, id=id_do_usuniecia)

        if not znaleziono:
            logger.debug(f'Użytkownik {ctx.author!r} chciał usunąć nieistniejące ID: {id_do_usuniecia!r}')
            await ctx.respond("Nie znaleziono zadania/ogłoszenia o podanym ID!")
            return

        znaleziono.task.cancel()
        self.bot.stan.lista_zadan.remove(znaleziono)
        logger.info(f'Użytkownik {ctx.author!r} usunął zadanie/ogłoszenie: {znaleziono!r}')

        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        if isinstance(znaleziono, ZadanieDomowe):
            await ctx.respond(**styl.formatuj_zadanie("Usunięto zadanie!", znaleziono))
        else:  # Jeśli nie zadanie, to ogłoszenie
            await ctx.respond(**styl.formatuj_ogloszenie("Usunięto ogłoszenie!", znaleziono))


def setup(bot: SpisBot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_cog(KomendyDlaEdytorow(bot))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
