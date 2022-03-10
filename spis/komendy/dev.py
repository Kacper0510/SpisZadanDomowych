from logging import getLogger
from typing import cast

from discord import commands, Bot

logger = getLogger("spis.komendy.global")

dev = commands.SlashCommandGroup("dev", "Komendy developerskie",
                                 permissions=[commands.CommandPermission("owner", 2, True)])


@dev.command()
async def zapisz(ctx: commands.ApplicationContext):
    """Zapisuje stan bota do pliku i wysyła go do twórcy bota"""

    sukces = await cast("SpisBot", ctx.bot).zapisz()
    await ctx.respond(f"Zapisanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)


@dev.command()
async def wczytaj(ctx: commands.ApplicationContext):
    """Wczytuje stan bota z kanału prywatnego twórcy bota (liczy się tylko ostatnia wiadomość)"""

    sukces = await cast("SpisBot", ctx.bot).wczytaj()
    await ctx.respond(f"Wczytanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)


def setup(bot: Bot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_application_command(cast("ApplicationCommand", dev))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
