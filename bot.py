# Created by RawandShaswar @ 08/06/2022, 7:00
from Classes import Dalle

# Builtin
import asyncio
import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import Union

# Discord
import discord

# PyYaml
import yaml
from discord import Embed
from discord.ext import commands

""" Load the configuration file """
with open("data.yaml") as f:
    c = yaml.safe_load(f)

# If windows, set policy
if os.name == 'nt':
    policy = asyncio.WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)

# Enforced intents.
bot_intents = discord.Intents.all()

def del_dir(target: Union[Path, str], only_if_empty: bool = False):
    """
    Delete a given directory and its subdirectories.

    :param target: The directory to delete
    :param only_if_empty: Raise RuntimeError if any file is found in the tree
    """
    target = Path(target).expanduser()
    if not target.is_dir():
        raise RuntimeError(f"{target} is not a directory")

    for p in sorted(target.glob('**/*'), reverse=True):
        if not p.exists():
            continue
        p.chmod(0o666)
        if p.is_dir():
            p.rmdir()
        else:
            if only_if_empty:
                raise RuntimeError(f'{p.parent} is not empty!')
            p.unlink()
    target.rmdir()


class DallEDiscordBot(commands.Bot):
    """
    Creates a discord bot.
    """

    def __init__(self, command_prefix, self_bot) -> None:
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot, intents=bot_intents)
        self.add_commands()

    def create_embed(self, guild) -> Embed:
        """
        Creates an embed object.
        :param guild:
        :return:
        """
        footer = self.get_footer()

        embed = discord.Embed(title=footer[0], color=footer[2])
        embed.set_author(name="https://huggingface.co", url="https://huggingface.co/spaces/dalle-mini/dalle-mini")

        embed.set_thumbnail(url=footer[1])
        embed.set_footer(text=footer[0], icon_url=footer[1])

        return embed

    @staticmethod
    def get_footer() -> list:
        """
        Gets the footer information from the config file.
        :return:
        """
        return [c['embed_title'], c['icon_url'], c['embed_color']]

    @staticmethod
    async def on_ready() -> None:
        """
        When the bot is ready.
        :return:
        """
        print("Made with ❤️ by Rawand Ahmed Shaswar in Kurdistan")
        print("Bot is online!\nCall !dalle <query>")

    @staticmethod
    async def _create_collage(ctx, query: str, source_image: Image, images: list) -> str:
        width = source_image.width
        height = source_image.height
        font_size = 30
        spacing = 16
        text_height = font_size + spacing
        new_im = Image.new('RGBA', (width * 3 + spacing * 2, height * 3 + spacing * 2 + text_height),
                           (0, 0, 0, 0))

        index = 0
        for i in range(0, 3):
            for j in range(0, 3):
                im = Image.open(images[index].path)
                im.thumbnail((width, height))
                new_im.paste(im, (i * (width + spacing), text_height + j * (height + spacing)))
                index += 1

        img_draw = ImageDraw.Draw(new_im)
        fnt = ImageFont.truetype("./FiraMono-Medium.ttf", font_size)
        img_draw.text((1, 0), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((0, 1), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((1, 2), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((2, 1), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((0, 0), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((0, 2), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((2, 0), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((2, 2), query, font=fnt, fill=(0, 0, 0))
        img_draw.text((1, 1), query, font=fnt, fill=(255, 255, 255))
        new_im.save(f"./generated/{ctx.author.id}/art.png")
        return f"./generated/{ctx.author.id}/art.png"

    def add_commands(self) -> None:

        @self.command(name="dalle", description="Generate dall-e images using your query.")
        async def execute(ctx, *, query) -> None:
            # Check if query is empty
            if not query:
                await ctx.message.reply("DALL·E: Invalid query\nPlease enter a query (e.g !dalle dogs on space).")
                return

            # Check if query is too long
            if len(query) > 100:
                await ctx.message.reply("DALL·E: Invalid query\nQuery is too long.")
                return

            print(f"[-] {ctx.author} called !dalle {query}")

            message = await ctx.message.reply("Generating DALL·E mini query (this make take up to 2 minutes):"
                                              " ```" + query + "```")

            try:
                dall_e = await Dalle.DallE(prompt=f"{query}", author=f"{ctx.author.id}")
                generated = await dall_e.generate()

                if len(generated) > 0:
                    first_image = Image.open(generated[0].path)
                    generated_collage = await self._create_collage(ctx, query, first_image, generated)

                    # Prepare the attachment
                    file = discord.File(generated_collage, filename="art.png")
                    await ctx.message.reply(file=file)

                    # Delete the message
                    await message.delete()

            except Dalle.DallENoImagesReturned:
                await ctx.message.reply(f"DALL·E mini api returned no images found for {query}.")
            except Dalle.DallENotJson:
                await ctx.message.reply("DALL·E API Serialization Error, please try again later.")
            except Dalle.DallEParsingFailed:
                await ctx.message.reply("DALL·E Parsing Error, please try again later.")
            except Dalle.DallESiteUnavailable:
                await ctx.message.reply("DALL·E API Error, please try again later.")
            except Exception as e:
                await ctx.message.reply("Internal Error, please try again later.")
                await ctx.message.reply(repr(e))
            finally:
                # Delete the author folder in ./generated with author id, if exists
                del_dir(f"./generated/{ctx.author.id}")

        @self.command(name="ping")
        async def ping(ctx) -> None:
            """
            Pings the bot.
            :param ctx:
            :return:
            """
            await ctx.message.reply("Pong!")

        @self.command(name="dallehelp", description="Shows the help menu.")
        async def help_command(ctx) -> None:
            """
            Displays the help command.
            :param ctx:
            :return:
            """
            await ctx.message.reply("""
            **Commands**:
                !dallehelp - shows this message
                !ping - pong!
                !dalle <query> - makes a request to the dall-e api and returns the result
            """)


async def background_task() -> None:
    """
    Any background tasks here.
    :return:
    """
    pass


bot = DallEDiscordBot(command_prefix=c['bot_prefix'], self_bot=False)
bot.loop.create_task(background_task())
bot.run(c['discord_token'])
