import discord
from discord.ext import commands
import wavelink
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} online!")
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.listening, name="/play 🎧")
    )
    node = wavelink.Node(uri='https://lava-v4.ajieblogs.eu.org:443', password='https://dsc.gg/ajidevserver')
    await wavelink.Pool.connect(client=bot, nodes=[node])
    await bot.tree.sync()

@bot.tree.command(name="play", description="Toca uma musica")
async def play(interaction: discord.Interaction, busca: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("Entra em um canal de voz!", ephemeral=True)
    if not interaction.guild.voice_client:
        await interaction.user.voice.channel.connect(cls=wavelink.Player)
    player = interaction.guild.voice_client
    tracks = await wavelink.Playable.search(busca)
    if not tracks:
        return await interaction.response.send_message("Nao achei nada", ephemeral=True)
    await interaction.response.send_message(f"Tocando: **{tracks[0].title}**")
    await player.play(tracks[0])

bot.run(os.getenv("DISCORD_TOKEN"))
