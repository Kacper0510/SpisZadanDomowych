from datetime import datetime
from logging import getLogger
from typing import cast

from discord import commands, embeds, ui, Bot

from ..main import OSTATNI_COMMIT

logger = getLogger("spis.komendy.global")


@commands.slash_command()
async def spis(
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

    cast("SpisBot", ctx.bot).stan.uzycia_spis += 1
    logger.debug(f"Użytkownik {repr(ctx.author)} wyświetlił spis")


@commands.slash_command()
async def info(ctx: commands.ApplicationContext):
    """Wyświetla statystyki i informacje o bocie"""
    bot = cast("SpisBot", ctx.bot)

    # Kolor przewodni wywołującego komendę
    kolor_uzytkownika = (await bot.fetch_user(ctx.author.id)).accent_color or embeds.EmptyEmbed
    embed = embeds.Embed(color=kolor_uzytkownika,
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
    przyciski = ui.View(
        ui.Button(
            label="Dodaj na serwer",
            url=bot.invite_link,
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


def setup(bot: Bot):
    """Wymagane przez pycorda do ładowania rozszerzenia"""
    bot.add_application_command(cast("ApplicationCommand", spis))
    bot.add_application_command(cast("ApplicationCommand", info))
    logger.debug(f"Wczytano komendy z rozszerzenia {__name__}")
