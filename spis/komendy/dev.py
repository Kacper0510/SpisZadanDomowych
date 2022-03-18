from logging import getLogger

from discord import commands, Cog

from ..bot import SpisBot
from ..main import bot as main_bot  # Chwilowe rozwiązanie

logger = getLogger(__name__)


class KomendyDeveloperskie(Cog):

    def __init__(self, bot: SpisBot):
        self.bot = bot

    dev = commands.SlashCommandGroup("dev", "Komendy developerskie", guild_ids=[main_bot.serwer_dev],
                                     permissions=[commands.CommandPermission("owner", 2, True)])

    @dev.command()
    async def zapisz(self, ctx: commands.ApplicationContext):
        """Zapisuje stan bota do pliku i wysyła go do twórcy bota"""

        sukces = await self.bot.zapisz()
        await ctx.respond(f"Zapisanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)

    @dev.command()
    async def wczytaj(self, ctx: commands.ApplicationContext):
        """Wczytuje stan bota z kanału prywatnego twórcy bota (liczy się tylko ostatnia wiadomość)"""

        sukces = await self.bot.wczytaj()
        await ctx.respond(f"Wczytanie się{'' if sukces else ' nie'} powiodło!", ephemeral=True)


def setup(bot: SpisBot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_cog(KomendyDeveloperskie(bot))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
