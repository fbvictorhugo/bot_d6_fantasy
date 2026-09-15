import os
import random
import re

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DICE = 2
DEFAULT_SIDES = 6
DEFAULT_MODIFIER = 0


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not found. Create a .env file with your token.")
    return token


def parse_roll_expression(expression: str = "") -> dict[str, int]:
    text = (expression or "").strip()

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
        raise ValueError(
            "Invalid format. Use examples like: 2d6, 1d20, 2d6 +1, 3d8-2 or +1."
        )

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
        raise ValueError("Dice quantity and sides must be greater than zero.")

    return {"dice": dice, "sides": sides, "modifier": modifier}


def roll_dice(dice_count: int, sides: int, modifier: int = 0) -> tuple[list[int], int]:
    rolls = [random.randint(1, sides) for _ in range(dice_count)]
    total = sum(rolls) + modifier
    return rolls, total


def is_d6_fantasy_roll(parsed: dict[str, int]) -> bool:
    return parsed["dice"] == 2 and parsed["sides"] == 6


def format_roll_result(expression: str):
    parsed = parse_roll_expression(expression)
    if is_d6_fantasy_roll(parsed):
        return format_d6_fantasy_result(parsed)
    return format_generic_roll_result(parsed)


def format_roll_expression_message(parsed: dict[str, int]) -> str:
    dice_count = parsed["dice"]
    sides = parsed["sides"]
    modifier = parsed["modifier"]
    modifier_text = (
        f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""
    )
    return f"_for a roll of: {dice_count}d{sides}{modifier_text}_"


def format_d6_fantasy_result(parsed: dict[str, int]) -> discord.Embed:
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

    modifier_text = (
        f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""
    )
    dice_text = ", ".join(str(value) for value in rolls)

    embed = discord.Embed(
        title=f"🎲 Result: [{dice_text}] + {modifier} = `{total}`",
        color=colour,
    )
    embed.set_footer(text="D6 Fantasy Express")
    return embed


def format_generic_roll_result(parsed: dict[str, int]) -> str:
    dice_count = parsed["dice"]
    sides = parsed["sides"]
    modifier = parsed["modifier"]
    rolls, total = roll_dice(dice_count, sides, modifier)

    modifier_text = (
        f" + {modifier}" if modifier > 0 else f" - {abs(modifier)}" if modifier < 0 else ""
    )
    dice_text = ", ".join(str(value) for value in rolls)

    return (
        f"🎲 Result: **[{dice_text}] + {modifier} = `{total}`**\n"
    )


class D6FantasyBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._setup_commands()

    def _setup_commands(self) -> None:
        @self.tree.command(name="roll", description="Roll dice for D6 Fantasy. Default: 2d6")
        @app_commands.describe(expression="Examples: 2d6, 3d8, 2d6 +1, 1d20")
        async def roll_command(
            interaction: discord.Interaction,
            expression: str = "2d6",
        ) -> None:
            try:
                parsed = parse_roll_expression(expression)
                result = format_roll_result(expression)
                msg_expression = format_roll_expression_message(parsed)
                if isinstance(result, discord.Embed):
                    await interaction.response.send_message(msg_expression, embed=result, ephemeral=False)
                else:
                    await interaction.response.send_message(msg_expression + "\n" + result, ephemeral=False)
            except ValueError as exc:
                await interaction.response.send_message(
                    f"⚠️ {exc}\nValid examples: `/roll`, `/roll 2d6`, `/roll 3d8`, `/roll 2d6 +1`.",
                    ephemeral=False,
                )

    async def on_ready(self) -> None:
        await self.tree.sync()
        print(f"Bot connected as {self.user} (ID: {self.user.id})")
        await self.change_presence(status=discord.Status.online, activity=discord.Game('RPG'))


def main() -> None:
    bot = D6FantasyBot()
    bot.run(get_discord_token())
