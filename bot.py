import discord
from discord.ext import commands
import wavelink
import os
from flask import Flask
import threading

app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "VainBot Online! 🟢"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} online!")
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Game(name="Eu não sou um cosplay kawai de Pikachu 😡")
    )
    try:
        nodes = [
            wavelink.Node(uri='https://lava-v4.ajieblogs.my.eu.org:443', password='https://dsc.gg/ajidevserver'),
            wavelink.Node(uri='http://lavalink.jirayu.net:13592', password='youshallnotpass'),
            wavelink.Node(uri='https://lavalinkv4-id.serenetia.com:443', password='https://dsc.gg/serenetia')
        ]
        await wavelink.Pool.connect(nodes=nodes, client=bot, cache_capacity=100)
        print("✅ Lavalink conectado!")
    except Exception as e:
        print(f"❌ Erro Lavalink: {e}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        print(e)

@bot.tree.command(name="tocar", description="Toca uma música")
async def play(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()
    if not interaction.user.voice:
        return await interaction.followup.send("Entra em um canal de voz primeiro! 🎧")
    try:
        player = interaction.guild.voice_client
        if not player:
            player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
        tracks = await wavelink.Playable.search(busca)
        if not tracks:
            return await interaction.followup.send(f"Não achei a música: {busca}")
        track = tracks[0]
        await player.queue.put_wait(track)
        if not player.playing:
            await player.play(player.queue.get())
        await interaction.followup.send(f"Tocando agora: **{track.title}** 🎶")
    except Exception as e:
        print(e)
        await interaction.followup.send(f"Erro: {e}")

bot.run(os.environ.get("DISCORD_TOKEN"))
