import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online como {bot.user}")

@bot.command()
async def ola(ctx):
    await ctx.send(f"Olá {ctx.author.mention}! Bot tá on!")

# Pega o token que vamos configurar no Koyeb
TOKEN = os.getenv("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
