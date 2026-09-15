import inspect
import os
import random
import re

import discord
from discord import app_commands
from dotenv import load_dotenv

from d6_bot.locale_manager import LocaleManager, DEFAULT_LOCALE

load_dotenv()

DEFAULT_DICE = 2
DEFAULT_SIDES = 6
DEFAULT_MODIFIER = 0
locale_manager = LocaleManager()


def resolve_locale(locale: str | object | None) -> str:
    return locale_manager.resolve_locale(locale)


def get_message(locale: str | None, key: str, **kwargs) -> str:
    return locale_manager.get_message(locale, key, **kwargs)


def resolve_interaction_locale(interaction: discord.Interaction | None) -> str:
    if interaction is None:
        return DEFAULT_LOCALE

    user_locale = getattr(interaction, "locale", None)
    guild_locale = getattr(getattr(interaction, "guild", None), "preferred_locale", None)
    return locale_manager.resolve_interaction_locale(user_locale, guild_locale)


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not found. Create a .env file with your token.")
    return token


def parse_roll_expression(expression: str = "", locale: str | None = None) -> dict[str, int]:
    text = (expression or "").strip()
    locale_name = resolve_locale(locale)

    if not text:
        return {"dice": DEFAULT_DICE, "sides": DEFAULT_SIDES, "modifier": DEFAULT_MODIFIER}

    if re.fullmatch(r"\d+", text, flags=re.IGNORECASE):
        return {"dice": DEFAULT_DICE, "sides": DEFAULT_SIDES, "modifier": int(text)}

    if re.fullmatch(r"[+-]\s*\d+", text, flags=re.IGNORECASE):
        modifier = 1 if text.strip().startswith("+") else -1
        modifier *= int(re.sub(r"[^\d]", "", text))
        return {"dice": DEFAULT_DICE, "sides": DEFAULT_SIDES, "modifier": modifier}

    match = re.fullmatch(
        r"(?:(?P<count>\d*)d(?P<sides>\d+)|(?P<single>\d+))\s*(?P<modifier>[+-]\s*\d+)?",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        raise ValueError(get_message(locale_name, "errors.invalid_format"))

    count_raw = match.group("count")
    sides_raw = match.group("sides")
    single_raw = match.group("single")
    modifier_raw = match.group("modifier") or ""

    if single_raw and not count_raw:
        dice = 1
        sides = int(single_raw)
    else:
        dice = int(count_raw or "1")
        sides = int(sides_raw or DEFAULT_SIDES)

    modifier = 0
    if modifier_raw:
        signal = 1 if modifier_raw.strip().startswith("+") else -1
        modifier = signal * int(re.sub(r"[^\d]", "", modifier_raw))

    if dice <= 0 or sides <= 0:
        raise ValueError(get_message(locale_name, "errors.dice_quantity"))

    return {"dice": dice, "sides": sides, "modifier": modifier}


def roll_dice(dice_count: int, sides: int, modifier: int = 0) -> tuple[list[int], int]:
    rolls = [random.randint(1, sides) for _ in range(dice_count)]
    total = sum(rolls) + modifier
    return rolls, total


def is_d6_fantasy_roll(parsed: dict[str, int]) -> bool:
    return parsed["dice"] == 2 and parsed["sides"] == 6


def format_roll_result(expression: str, locale: str | None = None):
    locale_name = resolve_locale(locale)
    parsed = parse_roll_expression(expression, locale=locale_name)
    if is_d6_fantasy_roll(parsed):
        return format_d6_fantasy_result(parsed, locale=locale_name)
    return format_generic_roll_result(parsed, locale=locale_name)


def format_roll_expression_message(parsed: dict[str, int], locale: str | None = None) -> str:
    locale_name = resolve_locale(locale)
    dice_count = parsed["dice"]
    sides = parsed["sides"]
    modifier = parsed["modifier"]
    modifier_text = (
        f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""
    )
    return get_message(
        locale_name,
        "roll.for_message",
        dice_count=dice_count,
        sides=sides,
        modifier_text=modifier_text,
    )


def format_d6_fantasy_result(parsed: dict[str, int], locale: str | None = None) -> discord.Embed:
    locale_name = resolve_locale(locale)
    dice_count = parsed["dice"]
    sides = parsed["sides"]
    modifier = parsed["modifier"]
    rolls, total = roll_dice(dice_count, sides, modifier)

    if total >= 10:
        colour = discord.Colour.green()
    elif total >= 7:
        colour = discord.Colour.yellow()
    else:
        colour = discord.Colour.red()

    dice_text = ", ".join(str(value) for value in rolls)
    title = get_message(
        locale_name,
        "roll.result",
        dice_text=dice_text,
        modifier=modifier,
        total=total,
    )

    embed = discord.Embed(
        title=title,
        color=colour,
    )
    embed.set_footer(text="D6 Fantasy Express")
    return embed


def format_generic_roll_result(parsed: dict[str, int], locale: str | None = None) -> str:
    locale_name = resolve_locale(locale)
    dice_count = parsed["dice"]
    sides = parsed["sides"]
    modifier = parsed["modifier"]
    rolls, total = roll_dice(dice_count, sides, modifier)

    dice_text = ", ".join(str(value) for value in rolls)
    return get_message(
        locale_name,
        "roll.generic_result",
        dice_text=dice_text,
        modifier=modifier,
        total=total,
    )


class D6FantasyBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._setup_commands()

    def _setup_commands(self) -> None:
        command_description = get_message(DEFAULT_LOCALE, "commands.roll.description")
        command_expression = get_message(DEFAULT_LOCALE, "commands.roll.expression")

        command_kwargs = {
            "name": "roll",
            "description": command_description,
        }

        signature = inspect.signature(self.tree.command)
        if "description_localizations" in signature.parameters:
            locale_map = {}
            en_locale = getattr(discord.Locale, "en_US", None) or getattr(discord.Locale, "american_english", None)
            pt_locale = getattr(discord.Locale, "pt_BR", None) or getattr(discord.Locale, "brazilian_portuguese", None)
            if en_locale is not None:
                locale_map[en_locale] = get_message("en-US", "commands.roll.description")
            if pt_locale is not None:
                locale_map[pt_locale] = get_message("pt-BR", "commands.roll.description")
            command_kwargs["description_localizations"] = locale_map

        @self.tree.command(**command_kwargs)
        @app_commands.describe(
            expression=command_expression,
        )
        async def roll_command(
            interaction: discord.Interaction,
            expression: str = "2d6",
        ) -> None:
            locale_name = resolve_interaction_locale(interaction)
            try:
                parsed = parse_roll_expression(expression, locale=locale_name)
                result = format_roll_result(expression, locale=locale_name)
                msg_expression = format_roll_expression_message(parsed, locale=locale_name)
                if isinstance(result, discord.Embed):
                    await interaction.response.send_message(msg_expression, embed=result, ephemeral=False)
                else:
                    await interaction.response.send_message(msg_expression + "\n" + result, ephemeral=False)
            except ValueError as exc:
                await interaction.response.send_message(
                    get_message(
                        locale_name,
                        "errors.invalid_usage",
                        message=str(exc),
                    ),
                    ephemeral=False,
                )

    async def on_ready(self) -> None:
        await self.tree.sync()
        guild_locales = sorted({str(guild.preferred_locale) for guild in self.guilds})
        print(f"Bot connected as {self.user} (ID: {self.user.id})")
        print(f"Guild locales detected: {guild_locales if guild_locales else ['none']}")
        await self.change_presence(status=discord.Status.online, activity=discord.Game("RPG"))


def main() -> None:
    bot = D6FantasyBot()
    bot.run(get_discord_token())
