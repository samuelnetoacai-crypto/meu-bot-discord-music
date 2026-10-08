import discord
from discord.ext import commands, app_commands
import os
import json
import random
import time
from datetime import timedelta
from flask import Flask
import threading

app_flask = Flask(__name__)
@app_flask.route('/')
def home():
    return "Online"
threading.Thread(target=app_flask.run, kwargs={'host':'0.0.0.0','port':int(os.environ.get("PORT", 10000))}, daemon=True).start()

BANCO_FILE = "banco.json"
DAILY_FILE = "daily.json"

def carregar_banco():
    if not os.path.exists(BANCO_FILE):
        return {}
    try:
        with open(BANCO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
def salvar_banco(banco):
    with open(BANCO_FILE, "w") as f:
        json.dump(banco, f)
def pegar_estrelas(user_id):
    return carregar_banco().get(str(user_id), 0)
def adicionar_estrelas(user_id, quantia):
    banco = carregar_banco()
    user_id = str(user_id)
    banco[user_id] = banco.get(user_id, 0) + quantia
    salvar_banco(banco)
    return banco[user_id]
def remover_estrelas(user_id, quantia):
    banco = carregar_banco()
    user_id = str(user_id)
    banco[user_id] = banco.get(user_id, 0) - quantia
    if banco[user_id] < 0:
        banco[user_id] = 0
    salvar_banco(banco)
    return banco[user_id]
def carregar_daily():
    if not os.path.exists(DAILY_FILE):
        return {}
    try:
        with open(DAILY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
def salvar_daily(daily):
    with open(DAILY_FILE, "w") as f:
        json.dump(daily, f)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Online {bot.user}")
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name="Eu não sou um cosplay kawai de Pikachu"))
    await bot.tree.sync()

# --- ECONOMIA ---
@bot.tree.command(name="banco", description="Veja quantas estrelas você tem")
async def banco(interaction: discord.Interaction):
    await interaction.response.send_message(f"{interaction.user.mention} você tem **{pegar_estrelas(interaction.user.id)} ⭐ estrelas**")

@bot.tree.command(name="daily", description="Pegue suas estrelas diárias!")
async def daily(interaction: discord.Interaction):
    daily_data = carregar_daily()
    uid = str(interaction.user.id)
    agora = time.time()
    if uid in daily_data and agora - daily_data[uid] < 86400:
        tr = 86400 - (agora - daily_data[uid])
        h, m = int(tr // 3600), int((tr % 3600) // 60)
        await interaction.response.send_message(embed=discord.Embed(title="Daily 💰", description=f"Calma {interaction.user.mention}! Volte em **{h}h {m}min**", color=0xFF0000), ephemeral=True)
        return
    ganho = random.randint(1200, 4000)
    total = adicionar_estrelas(interaction.user.id, ganho)
    daily_data[uid] = agora
    salvar_daily(daily_data)
    await interaction.response.send_message(embed=discord.Embed(title="Daily 💰", description=f"{interaction.user.mention} ganhou **{ganho} ⭐**! Total: **{total} ⭐**", color=0x00FF00))

@bot.tree.command(name="pagar", description="Dê estrelas para alguém")
async def pagar(interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
    if usuario.id == interaction.user.id or quantidade <= 0:
        await interaction.response.send_message("Quantidade inválida!", ephemeral=True)
        return
    if pegar_estrelas(interaction.user.id) < quantidade:
        await interaction.response.send_message(f"Sem saldo! Você tem {pegar_estrelas(interaction.user.id)} ⭐", ephemeral=True)
        return
    remover_estrelas(interaction.user.id, quantidade)
    adicionar_estrelas(usuario.id, quantidade)
    await interaction.response.send_message(embed=discord.Embed(title="Pagar 💸", description=f"{interaction.user.mention} pagou **{quantidade} ⭐** para {usuario.mention}!", color=0x00BFFF))

@bot.tree.command(name="rank", description="Veja o ranking de estrelas")
async def rank(interaction: discord.Interaction):
    banco = carregar_banco()
    if not banco:
        await interaction.response.send_message("Ninguém tem estrelas!", ephemeral=True)
        return
    ranking = sorted(banco.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'**{i}°**'} <@{uid}> - **{est} ⭐**\n" for i, (uid, est) in enumerate(ranking, 1)])
    await interaction.response.send_message(embed=discord.Embed(title="Estrelas Rank 🏆", description=desc, color=0xFFD700))

@bot.tree.command(name="editar-estrelas", description="")
@app_commands.default_permissions(administrator=True)
async def editar_estrelas(interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    if quantidade > 0:
        total = adicionar_estrelas(usuario.id, quantidade)
        await interaction.response.send_message(embed=discord.Embed(title="Editar 🛠️", description=f"Adicionado **{quantidade} ⭐** para {usuario.mention}! Total: **{total} ⭐**", color=0x00FF00), ephemeral=True)
    else:
        remover_estrelas(usuario.id, abs(quantidade))
        total = pegar_estrelas(usuario.id)
        await interaction.response.send_message(embed=discord.Embed(title="Editar 🛠️", description=f"Removido **{abs(quantidade)} ⭐** de {usuario.mention}! Total: **{total} ⭐**", color=0xFF0000), ephemeral=True)

# --- MODERAÇÃO ---
@bot.tree.command(name="banir", description="Bane um membro")
@app_commands.default_permissions(ban_members=True)
async def banir(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    try:
        await usuario.ban(reason=motivo)
        await interaction.response.send_message(embed=discord.Embed(title="Banido 🔨", description=f"{usuario.mention} foi banido!\n**Motivo:** {motivo}", color=0xFF0000))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="expulsar", description="Expulsa um membro")
@app_commands.default_permissions(kick_members=True)
async def expulsar(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    try:
        await usuario.kick(reason=motivo)
        await interaction.response.send_message(embed=discord.Embed(title="Expulso 👢", description=f"{usuario.mention} foi expulso!\n**Motivo:** {motivo}", color=0xFFA500))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="mutar", description="Muta um membro por um tempo")
@app_commands.default_permissions(moderate_members=True)
async def mutar(interaction: discord.Interaction, usuario: discord.Member, minutos: int, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    if minutos <= 0 or minutos > 10080:
        await interaction.response.send_message("Use 1 a 10080 minutos", ephemeral=True)
        return
    try:
        await usuario.timeout(timedelta(minutes=minutos), reason=motivo)
        h, m = minutos // 60, minutos % 60
        fmt = f"{h}h {m}min" if h and m else f"{h}h" if h else f"{m}min"
        await interaction.response.send_message(embed=discord.Embed(title="Mutado 🔇", description=f"{usuario.mention} foi mutado por **{fmt}** ({minutos} min)!\n**Motivo:** {motivo}", color=0x808080))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="desmutar", description="Desmuta um membro")
@app_commands.default_permissions(moderate_members=True)
async def desmutar(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    try:
        await usuario.timeout(None)
        await interaction.response.send_message(embed=discord.Embed(title="Desmutado 🔊", description=f"{usuario.mention} foi desmutado!", color=0x00FF00))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="limpar", description="Apaga uma quantidade de mensagens")
@app_commands.default_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Você não tem permissão pra apagar mensagens!", ephemeral=True)
        return
    if quantidade <= 0 or quantidade > 100:
        await interaction.response.send_message("Use um número entre 1 e 100!", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        apagadas = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(embed=discord.Embed(title="Limpar 🧹", description=f"Apagadas **{len(apagadas)}** mensagens!", color=0x00BFFF), ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Erro ao limpar: {e}", ephemeral=True)

bot.run(os.environ.get("DISCORD_TOKEN"))
