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

from datetime import datetime
from logging import getLogger

from discord import commands, embeds, ui, Cog

from ..bot import SpisBot
from ..style import DOMYSLNY_STYL

logger = getLogger(__name__)


class KomendyGlobalne(Cog):

    def __init__(self, bot: SpisBot):
        self.bot = bot

    @commands.slash_command()
    async def spis(
            self,
            ctx: commands.ApplicationContext,
            wyswietl_wszystkim: commands.Option(
                str,
                "Czy wiadomość ma być wysłana jako widoczna dla wszystkich?",
                choices=["Tak", "Nie (domyślnie)"],
                default="Nie (domyślnie)"
            )
    ):
        """Wyświetla aktualny stan spisu"""
        wyswietl_wszystkim = wyswietl_wszystkim == "Tak"  # Cast na bool
        styl = self.bot.stan.style.get(ctx.author.id, DOMYSLNY_STYL)
        await ctx.respond(**styl.formatuj_spis(self.bot.stan.lista_zadan), ephemeral=not wyswietl_wszystkim)

        self.bot.stan.uzycia_spis += 1
        logger.debug(f"Użytkownik {ctx.author!r} wyświetlił spis")

    # # Jednak nie działa to tak dobrze, jak chciałem...
    # @commands.slash_command()
    # async def s(self, ctx: commands.ApplicationContext):
    #     """Alias komendy /spis"""
    #     await self.spis(ctx, "Nie (domyślnie)")

    @commands.slash_command()
    async def info(self, ctx: commands.ApplicationContext):
        """Wyświetla statystyki i informacje o bocie"""

        # Kolor przewodni wywołującego komendę
        kolor_uzytkownika = (await self.bot.fetch_user(ctx.author.id)).accent_color or embeds.EmptyEmbed
        embed = embeds.Embed(color=kolor_uzytkownika,
                             title="Informacje o bocie",
                             url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")  # Rickroll, bo czemu nie XD
        embed.set_thumbnail(url=self.bot.user.avatar.url)  # Miniatura - profilowe bota

        # Pola embeda
        embed.add_field(name="Twórca bota", value=str(self.bot.backup_kanal.recipient), inline=False)

        embed.add_field(name="Ping", value=f"{round(self.bot.latency * 1000)} ms")
        uptime = str(datetime.now() - self.bot.czas_startu)
        if kropka := uptime.find("."):  # Pozbywamy się mikrosekund
            uptime = uptime[:kropka]
        embed.add_field(name="Czas pracy", value=uptime)
        embed.add_field(name="Serwery", value=str(len(self.bot.guilds)))

        embed.add_field(name="Ostatni backup", value=f"<t:{round(self.bot.stan.ostatni_zapis.timestamp())}:R>")
        embed.add_field(name="Globalna ilość użyć `/spis`", value=str(self.bot.stan.uzycia_spis))

        if self.bot.ostatni_commit:
            embed.add_field(name="Ostatnia aktualizacja", value=self.bot.ostatni_commit, inline=False)

        # Przyciski pod wiadomością
        przyciski = ui.View(
            ui.Button(
                label="Dodaj na serwer",
                url=self.bot.invite_link,
                emoji="📲"
            ),
            ui.Button(
                label="Kod źródłowy i informacje",
                url="https://github.com/Kacper0510/SpisZadanDomowych",
                emoji="⌨"
            ),
            timeout=None
        )

        await ctx.respond(embed=embed, ephemeral=True, view=przyciski)
        logger.debug(f"Użytkownik {ctx.author!r} wyświetlił informacje o bocie")


def setup(bot: SpisBot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_cog(KomendyGlobalne(bot))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
