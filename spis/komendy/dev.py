#  MIT License
#
#  Copyright (c) 2023 Kacper Wojciuch
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

from logging import getLogger

from discord import commands, Cog, Permissions

from ..bot import SpisBot

logger = getLogger(__name__)


class KomendyDeveloperskie(Cog):

    def __init__(self, bot: SpisBot):
        self.bot = bot
        if bot.serwer_dev is not None:
            self.__cog_commands__[0].guild_ids = [bot.serwer_dev]  # Nadpisanie guild_ids dla dev

    dev = commands.SlashCommandGroup("dev", "Komendy developerskie",
                                     default_member_permissions=Permissions(1 << 3))  # ADMINISTRATOR

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
