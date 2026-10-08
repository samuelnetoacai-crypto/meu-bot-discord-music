import discord
from discord.ext import commands
import os
import json
import random
import time
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
    banco = carregar_banco()
    return banco.get(str(user_id), 0)
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

@bot.tree.command(name="banco", description="Veja quantas estrelas você tem")
async def banco(interaction: discord.Interaction):
    estrelas = pegar_estrelas(interaction.user.id)
    await interaction.response.send_message(f"{interaction.user.mention} você tem **{estrelas} ⭐ estrelas**")

@bot.tree.command(name="daily", description="Pegue suas estrelas diárias!")
async def daily(interaction: discord.Interaction):
    daily_data = carregar_daily()
    user_id = str(interaction.user.id)
    agora = time.time()
    if user_id in daily_data:
        if agora - daily_data[user_id] < 86400:
            tempo_restante = 86400 - (agora - daily_data[user_id])
            horas = int(tempo_restante // 3600)
            minutos = int((tempo_restante % 3600) // 60)
            await interaction.response.send_message(embed=discord.Embed(title="Daily 💰", description=f"Calma {interaction.user.mention}! Você já pegou seu daily.\nVolte em **{horas}h {minutos}min**", color=0xFF0000), ephemeral=True)
            return
    ganho = random.randint(1200, 4000)
    total = adicionar_estrelas(interaction.user.id, ganho)
    daily_data[user_id] = agora
    salvar_daily(daily_data)
    await interaction.response.send_message(embed=discord.Embed(title="Daily 💰", description=f"{interaction.user.mention} você ganhou **{ganho} ⭐**!\nAgora você tem **{total} ⭐ estrelas**", color=0x00FF00))

@bot.tree.command(name="pagar", description="Dê uma quantidade de estrelas específica para algum usuário")
async def pagar(interaction: discord.Interaction, usuario: discord.Member, quantidade: int):
    if usuario.id == interaction.user.id:
        await interaction.response.send_message(embed=discord.Embed(title="Pagar Estrelas", description="Você não pode pagar para si mesmo!", color=0xFF0000), ephemeral=True)
        return
    if quantidade <= 0:
        await interaction.response.send_message(embed=discord.Embed(title="Pagar Estrelas", description="A quantidade tem que ser maior que 0!", color=0xFF0000), ephemeral=True)
        return
    saldo = pegar_estrelas(interaction.user.id)
    if saldo < quantidade:
        await interaction.response.send_message(embed=discord.Embed(title="Pagar Estrelas", description=f"Você não tem estrelas suficientes! Você tem **{saldo} ⭐**", color=0xFF0000), ephemeral=True)
        return
    remover_estrelas(interaction.user.id, quantidade)
    adicionar_estrelas(usuario.id, quantidade)
    saldo_novo = pegar_estrelas(interaction.user.id)
    await interaction.response.send_message(embed=discord.Embed(title="Pagar Estrelas 💸", description=f"{interaction.user.mention} pagou **{quantidade} ⭐** para {usuario.mention}!\nAgora você tem **{saldo_novo} ⭐ estrelas**", color=0x00BFFF))

@bot.tree.command(name="rank", description="Veja o ranking de pessoas com mais estrelas no servidor")
async def rank(interaction: discord.Interaction):
    banco = carregar_banco()
    if not banco:
        await interaction.response.send_message(embed=discord.Embed(title="Estrelas Rank 🏆", description="Ninguém tem estrelas ainda!", color=0xFFFF00))
        return
    ranking = sorted(banco.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for i, (user_id, estrelas) in enumerate(ranking, start=1):
        medalha = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"**{i}°**"
        try:
            user = await bot.fetch_user(int(user_id))
            nome = user.name
        except:
            nome = f"ID {user_id}"
        extra = " 👈 você" if str(interaction.user.id) == user_id else ""
        desc += f"{medalha} {nome} - **{estrelas} ⭐**{extra}\n"
    embed = discord.Embed(title="Estrelas Rank 🏆", description=desc, color=0xFFD700)
    await interaction.response.send_message(embed=embed)

bot.run(os.environ.get("DISCORD_TOKEN"))
