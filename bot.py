import discord
from discord.ext import commands
import os
import yt_dlp
from flask import Flask
import threading

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "VainBot Online! 🟢"
threading.Thread(target=app_flask.run, kwargs={'host':'0.0.0.0','port':int(os.environ.get("PORT", 10000))}, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents) # AQUI MUDEI PRA *

yt_opts = {'format': 'bestaudio', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} online!")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name="Eu não sou um cosplay kawai de Pikachu 😡"))
    await bot.tree.sync()

@bot.tree.command(name="tocar", description="Toca uma música")
async def tocar(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()
    if not interaction.user.voice:
        return await interaction.followup.send("Entra em um canal de voz primeiro! 🎧")
    voice = interaction.guild.voice_client
    if not voice:
        voice = await interaction.user.voice.channel.connect()
    with yt_dlp.Y
