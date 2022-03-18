from datetime import datetime
from logging import getLogger

from discord import commands, embeds, ui, Cog

from ..bot import SpisBot

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
        await ctx.respond("to jeszcze nie jest zaimplementowane lol", ephemeral=not wyswietl_wszystkim)

        self.bot.stan.uzycia_spis += 1
        logger.debug(f"Użytkownik {repr(ctx.author)} wyświetlił spis")

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
        embed.add_field(name="Serwery", value=len(self.bot.guilds))

        embed.add_field(name="Ostatni backup", value=f"<t:{round(self.bot.stan.ostatni_zapis.timestamp())}:R>")
        embed.add_field(name="Globalna ilość użyć `/spis`", value=self.bot.stan.uzycia_spis)

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
        logger.debug(f"Użytkownik {repr(ctx.author)} wyświetlił informacje o bocie")


def setup(bot: SpisBot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_cog(KomendyGlobalne(bot))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
