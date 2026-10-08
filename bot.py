import discord
from discord.ext import commands
import os
import yt_dlp
import asyncio
from flask import Flask
import threading

app_flask = Flask(__name__)
@app_flask.route('/')
def home(): return "Online"
threading.Thread(target=app_flask.run, kwargs={'host':'0.0.0.0','port':int(os.environ.get("PORT", 10000))}, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="*", intents=intents)

@bot.event
async def on_ready():
    print(f"Online {bot.user}")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name="Eu não sou um cosplay kawai de Pikachu"))
    await bot.tree.sync()

@bot.tree.command(name="tocar", description="Toca musica")
async def tocar(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()
    try:
        if not interaction.user.voice:
            return await interaction.followup.send("Entra em call!")
        vc = interaction.guild.voice_client
        if not vc:
            vc = await interaction.user.voice.channel.connect()

        def get_info():
            ydl_opts = {'format':'bestaudio','noplaylist':True,'quiet':True,'default_search':'ytsearch'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(busca, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                return info

        info = await asyncio.to_thread(get_info)
        url = info['url']
        title = info.get('title', busca)

        ffmpeg = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(url, **ffmpeg))
        await interaction.followup.send(f"Tocando: **{title}**")
    except Exception as e:
        print(f"ERRO: {e}")
        await interaction.followup.send(f"Deu erro aqui: {e}")

@bot.tree.command(name="parar", description="Para")
async def parar(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Parei!")
    else:
        await interaction.response.send_message("Nem to em call")

bot.run(os.environ.get("DISCORD_TOKEN"))
