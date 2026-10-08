import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import random
import time
from datetime import timedelta
from flask import Flask
import threading
import json, os, random
from datetime import datetime, timedelta

# Servidor fake pro Render não dormir
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
    await bot.change_presence(status=discord.Status.idle, activity=discord.Game(name="Vou eletrocutar quem quebrar as regras"))
    try:
        synced = await bot.tree.sync()
        print(f"Syncou {len(synced)} comandos globais")
        for guild in bot.guilds:
            await bot.tree.sync(guild=guild)
            print(f"Syncou instantaneo em {guild.name}")
    except Exception as e:
        print(f"Erro sync: {e}")

# --- ECONOMIA ---
@bot.tree.command(name="ver_banco", description="Veja quantas estrelas você tem")
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

@bot.tree.command(name="pay", description="Dê estrelas para alguém")
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

@bot.tree.command(name="estrelas_rank", description="Veja o ranking de estrelas no servidor")
async def rank(interaction: discord.Interaction):
    banco = carregar_banco()
    if not banco:
        await interaction.response.send_message("Ninguém tem estrelas!", ephemeral=True)
        return
    ranking = sorted(banco.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = "".join([f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'**{i}°**'} <@{uid}> - **{est} ⭐**\n" for i, (uid, est) in enumerate(ranking, 1)])
    await interaction.response.send_message(embed=discord.Embed(title="Estrelas Rank 🏆", description=desc, color=0xFFD700))

@bot.tree.command(name="editar_estrelas", description="Editar estrelas de um membro")
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
@bot.tree.command(name="ban", description="Bane um membro do servidor")
@app_commands.default_permissions(ban_members=True)
async def banir(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("Você não tem permissão!", ephemeral=True)
        return
    try:
        await usuario.ban(reason=motivo)
        await interaction.response.send_message(embed=discord.Embed(title="Banido 🔨", description=f"{usuario.mention} foi banido!\n**Motivo:** {motivo}", color=0xFF0000))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="expulsar", description="Expulsa um membro do servidor")
@app_commands.default_permissions(kick_members=True)
async def expulsar(interaction: discord.Interaction, usuario: discord.Member, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("Você não tem permissão!", ephemeral=True)
        return
    try:
        await usuario.kick(reason=motivo)
        await interaction.response.send_message(embed=discord.Embed(title="Expulso 👢", description=f"{usuario.mention} foi expulso!\n**Motivo:** {motivo}", color=0xFFA500))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="mute", description="Muta um membro por um tempo")
@app_commands.default_permissions(moderate_members=True)
async def mutar(interaction: discord.Interaction, usuario: discord.Member, minutos: int, motivo: str = "Sem motivo"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("Sem permissão!", ephemeral=True)
        return
    if minutos <= 0 or minutos > 10080:
        await interaction.response.send_message("Use de 1 a 10080 minutos (7 dias)", ephemeral=True)
        return
    try:
        await usuario.timeout(timedelta(minutes=minutos), reason=motivo)
        h, m = minutos // 60, minutos % 60
        fmt = f"{h}h {m}min" if h and m else f"{h}h" if h else f"{m}min"
        await interaction.response.send_message(embed=discord.Embed(title="Mutado 🔇", description=f"{usuario.mention} foi mutado por **{fmt}** ({minutos} min)!\n**Motivo:** {motivo}", color=0x808080))
    except Exception as e:
        await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="desmute", description="Desmuta um membro")
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

@bot.tree.command(name="limpar_mensagens", description="Apaga uma quantidade de mensagens")
@app_commands.default_permissions(manage_messages=True)
async def limpar(interaction: discord.Interaction, quantidade: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("Você não tem permissão pra apagar!", ephemeral=True)
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
ROUBO_FILE = "roubo.json"
CAIXA_FILE = "caixa.json"

def carregar_roubo():
    if not os.path.exists(ROUBO_FILE):
        return {}
    try:
        with open(ROUBO_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def salvar_roubo(data):
    with open(ROUBO_FILE, "w") as f:
        json.dump(data, f)

def carregar_caixa():
    if not os.path.exists(CAIXA_FILE):
        return {}
    try:
        with open(CAIXA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def salvar_caixa(data):
    with open(CAIXA_FILE, "w") as f:
        json.dump(data, f)

@bot.tree.command(name="roubar", description="Tente roubar os sonhos de alguém!")
async def roubar(interaction: discord.Interaction, vitima: discord.Member):
    try:
        if vitima.id == interaction.user.id or vitima.bot:
            await interaction.response.send_message("Alvo inválido!", ephemeral=True)
            return

        if not os.path.exists(ROUBO_FILE):
            salvar_roubo({})

        roubo_data = carregar_roubo()
        uid = str(interaction.user.id)
        vid = str(vitima.id)
        agora = time.time()

        historico = roubo_data.get(uid, [])
        historico = [h for h in historico if agora - h['tempo'] < 86400]

        if len(historico) >= 3:
            proximo = min(h['tempo'] for h in historico) + 86400
            falta = int(proximo - agora)
            h = falta // 3600
            m = (falta % 3600) // 60
            await interaction.response.send_message(f"Limite diário! Você já fez 3 roubos hoje. Volta em **{h}h {m}m** ⏳", ephemeral=True)
            return

        for h in historico:
            if h['vitima'] == vid:
                falta = int(86400 - (agora - h['tempo']))
                hh = falta // 3600
                await interaction.response.send_message(f"Você já roubou {vitima.mention} hoje! Espere **{hh}h** pra roubar de novo 🔒", ephemeral=True)
                return

        if pegar_estrelas(vitima.id) < 1200:
            await interaction.response.send_message(f"{vitima.mention} tem menos de 1200 ⭐", ephemeral=True)
            return
        if pegar_estrelas(interaction.user.id) < 200:
            await interaction.response.send_message(f"Você precisa de 200 ⭐ pra roubar", ephemeral=True)
            return

        historico.append({"vitima": vid, "tempo": agora})
        roubo_data[uid] = historico
        salvar_roubo(roubo_data)

        if random.random() < 0.30:
            quantia = random.randint(1200, 4000)
            quantia = min(quantia, pegar_estrelas(vitima.id))
            remover_estrelas(vitima.id, quantia)
            adicionar_estrelas(interaction.user.id, quantia)
            await interaction.response.send_message(embed=discord.Embed(
                title="Roubo Sucesso! 🦹‍♂️",
                description=f"{interaction.user.mention} roubou **{quantia} ⭐** de {vitima.mention}! 💰\nRoubos hoje: {len(historico)}/3",
                color=0x00FF00))
        else:
            multa = random.randint(100, 300)
            remover_estrelas(interaction.user.id, multa)
            await interaction.response.send_message(embed=discord.Embed(
                title="Roubo Falhou! 🚨",
                description=f"{interaction.user.mention} foi pego tentando roubar {vitima.mention} e perdeu **{multa} ⭐**!\nRoubos hoje: {len(historico)}/3 (70% falha)",
                color=0xFF0000))

    except Exception as e:
        print(f"ERRO roubar: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Erro: {e}", ephemeral=True)

@bot.tree.command(name="roleta_ratinho", description="Gire a roleta e aposte suas estrelas")
@app_commands.describe(quantidade="Quanto vai apostar", escolha="vermelho, preto, ou um numero de 0 a 14")
async def roleta(interaction: discord.Interaction, quantidade: int, escolha: str):
    escolha = escolha.lower()
    if quantidade < 20 or pegar_estrelas(interaction.user.id) < quantidade:
        await interaction.response.send_message(f"Saldo insuficiente! Você tem {pegar_estrelas(interaction.user.id)} ⭐ | Mínimo 20", ephemeral=True)
        return
    numero = random.randint(0, 14)
    cor = "verde" if numero == 0 else "vermelho" if numero % 2 == 0 else "preto"
    emoji = "🟢" if cor == "verde" else "🔴" if cor == "vermelho" else "⚫"
    if escolha in ["vermelho", "preto"]:
        if escolha == cor:
            ganho = quantidade * 2
            remover_estrelas(interaction.user.id, quantidade)
            adicionar_estrelas(interaction.user.id, ganho)
            await interaction.response.send_message(embed=discord.Embed(title=f"Roleta {emoji} {numero} - {cor}", description=f"Ganhou! Apostou {quantidade} ⭐ em **{escolha}** e levou **{ganho} ⭐** (2x)", color=0x00FF00))
        else:
            remover_estrelas(interaction.user.id, quantidade)
            await interaction.response.send_message(embed=discord.Embed(title=f"Roleta {emoji} {numero} - {cor}", description=f"Perdeu! Apostou em **{escolha}** e deu **{cor}**. Perdeu {quantidade} ⭐", color=0xFF0000))
    elif escolha.isdigit() and 0 <= int(escolha) <= 14:
        if int(escolha) == numero:
            ganho = quantidade * 14
            remover_estrelas(interaction.user.id, quantidade)
            adicionar_estrelas(interaction.user.id, ganho)
            await interaction.response.send_message(embed=discord.Embed(title=f"Roleta 🎰 JACKPOT {numero}!", description=f"{interaction.user.mention} ACERTOU O NÚMERO! {quantidade} ⭐ viraram **{ganho} ⭐** (14x) 🤯", color=0xFFD700))
        else:
            remover_estrelas(interaction.user.id, quantidade)
            await interaction.response.send_message(embed=discord.Embed(title=f"Roleta {emoji} {numero} - {cor}", description=f"Quase! Você escolheu **{escolha}** e deu **{numero}**. Perdeu {quantidade} ⭐", color=0x808080))
    else:
        await interaction.response.send_message("Escolha inválida! Use `vermelho`, `preto` ou um número de `0` a `14`", ephemeral=True)

@bot.tree.command(name="caixa_misteriosa", description="Abra uma caixa misteriosa por 500 estrelas")
async def caixa_misteriosa(interaction: discord.Interaction):
    preco = 500
    if pegar_estrelas(interaction.user.id) < preco:
        await interaction.response.send_message(f"Precisa de {preco} ⭐! Você tem {pegar_estrelas(interaction.user.id)} ⭐", ephemeral=True)
        return

    caixa_data = carregar_caixa()
    uid = str(interaction.user.id)
    agora = time.time()

    # Pega usos das ultimas 24h
    usos = caixa_data.get(uid, [])
    usos_recentes = [t for t in usos if agora - t < 86400]

    if len(usos_recentes) >= 2:
        proximo = min(usos_recentes) + 86400
        falta = int((proximo - agora) // 3600)
        await interaction.response.send_message(f"Você já abriu 2 caixas nas últimas 24h! Volta em **{falta}h** 📦🔒", ephemeral=True)
        return

    remover_estrelas(interaction.user.id, preco)

    sorte = random.random()
    if sorte < 0.60:
        ganho = random.randint(10, 400)
        cor = 0xFF0000
        msg = "Caixa meio vazia... 😭"
    elif sorte < 0.90:
        ganho = random.randint(500, 1200)
        cor = 0x00BFFF
        msg = "Boa! Lucro médio! ✨"
    elif sorte < 0.99:
        ganho = random.randint(1200, 3000)
        cor = 0xA020F0
        msg = "CAIXA RARA! 💜"
    else:
        ganho = random.randint(3000, 8000)
        cor = 0xFFD700
        msg = "CAIXA LENDÁRIA DOURADA!!! 👑🤯"

    adicionar_estrelas(interaction.user.id, ganho)
    usos_recentes.append(agora)
    caixa_data[uid] = usos_recentes
    salvar_caixa(caixa_data)

    lucro = ganho - preco
    await interaction.response.send_message(embed=discord.Embed(
        title=f"Caixa Misteriosa 📦 {msg}",
        description=f"{interaction.user.mention} pagou {preco} ⭐ e ganhou **{ganho} ⭐**!\n**Lucro:** {lucro} ⭐ | Usos hoje: {len(usos_recentes)}/2" if lucro >= 0 else f"{interaction.user.mention} pagou {preco} ⭐ e ganhou só **{ganho} ⭐**!\n**Prejuízo:** {lucro} ⭐ | Usos hoje: {len(usos_recentes)}/2",
        color=cor
    ))
@bot.tree.command(name="criar_embed", description="Cria um embed personalizado")
@app_commands.describe(
    titulo="Título do embed",
    descricao="Texto/descrição do embed",
    cor="Cor em hexadecimal ex: #FFD700 ou #FF0000 (padrão amarelo)",
    imagem="Link da imagem (opcional)",
    canal="Canal onde enviar o embed (opcional, padrão: aqui)"
)
async def criar_embed(interaction: discord.Interaction, titulo: str, descricao: str, cor: str = "#FFD700", imagem: str = None, canal: discord.TextChannel = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Você precisa ter permissão de **Administrador** pra usar isso! 🔒", ephemeral=True)
        return

    try:
        cor_limpa = cor.replace("#", "").strip()
        cor_final = int(cor_limpa, 16)
    except:
        await interaction.response.send_message(f"Cor inválida `{cor}`! Use formato #FFD700", ephemeral=True)
        return

    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=cor_final
    )

    if imagem:
        embed.set_image(url=imagem)

    destino = canal if canal else interaction.channel

    try:
        await destino.send(embed=embed)
        await interaction.response.send_message(f"Embed enviado em {destino.mention} ✅", ephemeral=True)
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"Erro! Verifica o link da imagem e se tenho permissão no {destino.mention}\n`{e}`", ephemeral=True)
        else:
            await interaction.followup.send(f"Erro! `{e}`", ephemeral=True)
# ================= MINERAÇÃO =================
MINERIOS = [
    {"nome": "Pedra", "emoji": "🪨", "chance": 30, "valor": 100, "tier": 1},
    {"nome": "Carvão", "emoji": "⚫", "chance": 20, "valor": 300, "tier": 1},
    {"nome": "Cobre", "emoji": "🟠", "chance": 15, "valor": 600, "tier": 2},
    {"nome": "Ferro", "emoji": "⛓️", "chance": 12, "valor": 1400, "tier": 2},
    {"nome": "Ouro", "emoji": "🟡", "chance": 8, "valor": 3000, "tier": 3},
    {"nome": "Lapis Lazuli", "emoji": "🔵", "chance": 5, "valor": 6000, "tier": 3},
    {"nome": "Redstone", "emoji": "🔴", "chance": 4, "valor": 10000, "tier": 3},
    {"nome": "Esmeralda", "emoji": "🟢", "chance": 2.5, "valor": 20000, "tier": 4},
    {"nome": "Diamante", "emoji": "💎", "chance": 1.5, "valor": 40000, "tier": 4},
    {"nome": "Netherita", "emoji": "⬛", "chance": 0.7, "valor": 150000, "tier": 5},
    {"nome": "Cristal do Vazio", "emoji": "🌌", "chance": 0.3, "valor": 500000, "tier": 5},
]
PICARETAS = {
    1: {"nome": "Madeira", "preco": 0, "multiplicador": 1, "emoji": "🪵", "max_tier": 1},
    2: {"nome": "Pedra", "preco": 20000, "multiplicador": 1.5, "emoji": "🪨", "max_tier": 2},
    3: {"nome": "Ferro", "preco": 50000, "multiplicador": 2, "emoji": "⛓️", "max_tier": 3},
    4: {"nome": "Ouro", "preco": 100000, "multiplicador": 2.5, "emoji": "🟡", "max_tier": 3},
    5: {"nome": "Diamante", "preco": 250000, "multiplicador": 3, "emoji": "💎", "max_tier": 4},
    6: {"nome": "Netherita", "preco": 500000, "multiplicador": 4.5, "emoji": "⬛", "max_tier": 5},
    7: {"nome": "Vazio", "preco": 1000000, "multiplicador": 7, "emoji": "🌌", "max_tier": 5},
}
ARQUIVO_MINERACAO = "inventario.json"

def carregar_dados():
    if not os.path.exists(ARQUIVO_MINERACAO): return {}
    with open(ARQUIVO_MINERACAO, "r") as f: return json.load(f)
def salvar_dados(d):
    with open(ARQUIVO_MINERACAO, "w") as f: json.dump(d, f, indent=4)
def sortear_minerio(lvl):
    max_tier = PICARETAS[lvl]["max_tier"]
    possiveis = [m for m in MINERIOS if m["tier"] <= max_tier]
    return random.choices(possiveis, weights=[m["chance"] for m in possiveis], k=1)[0]

@bot.tree.command(name="minerar", description="Minere para conseguir estrelas!")
async def minerar(interaction: discord.Interaction):
    dados = carregar_dados()
    uid = str(interaction.user.id)
    if uid not in dados:
        dados[uid] = {"minerios": {}, "estrelas": 0, "picareta": 1, "min_dia": 0, "ultimo_reset": datetime.now().isoformat()}
    ultimo = datetime.fromisoformat(dados[uid]["ultimo_reset"])
    if datetime.now() - ultimo >= timedelta(hours=24):
        dados[uid]["min_dia"] = 0
        dados[uid]["ultimo_reset"] = datetime.now().isoformat()
    if dados[uid]["min_dia"] >= 10:
        resto = (ultimo + timedelta(hours=24) - datetime.now()).seconds // 3600
        await interaction.response.send_message(f"⛏️ Limite diário! Volta em {resto}h.", ephemeral=True)
        return
    minerio = sortear_minerio(dados[uid]["picareta"])
    dados[uid]["minerios"][minerio["nome"]] = dados[uid]["minerios"].get(minerio["nome"], 0) + 1
    dados[uid]["min_dia"] += 1
    salvar_dados(dados)
    embed = discord.Embed(title=f"⛏️ {minerio['emoji']} {minerio['nome']}!", description=f"Valor: {minerio['valor']} ⭐\nRestam {10-dados[uid]['min_dia']}/10 hoje.", color=0x2b2d31)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="inventário", description="Veja seus minérios")
async def inventario(interaction: discord.Interaction):
    dados = carregar_dados()
    u = dados.get(str(interaction.user.id))
    if not u or not u["minerios"]:
        await interaction.response.send_message("📦 Vazio. Use /minerar", ephemeral=True)
        return
    desc = f"⛏️ **{PICARETAS[u['picareta']]['emoji']} {PICARETAS[u['picareta']]['nome']}** | ⭐ {u['estrelas']}\n\n"
    total = 0
    for nome, qtd in u["minerios"].items():
        info = next(m for m in MINERIOS if m["nome"] == nome)
        desc += f"{info['emoji']} {nome}: {qtd}x ({info['valor']*qtd} ⭐)\n"
        total += info['valor']*qtd
    desc += f"\n**Total se vender tudo: {total} ⭐**"
    await interaction.response.send_message(embed=discord.Embed(title=f"Inventário - {interaction.user.display_name}", description=desc, color=0x2b2d31))

@bot.tree.command(name="vender_Tudo", description="Venda TODOS os minérios")
async def vender_tudo(interaction: discord.Interaction):
    dados = carregar_dados()
    uid = str(interaction.user.id)
    if uid not in dados or not dados[uid]["minerios"]:
        await interaction.response.send_message("📦 Nada pra vender.", ephemeral=True)
        return
    total = 0
    lista = []
    for nome, qtd in list(dados[uid]["minerios"].items()):
        info = next(m for m in MINERIOS if m["nome"] == nome)
        total += info["valor"] * qtd
        lista.append(f"{info['emoji']} {nome} x{qtd}")
    dados[uid]["minerios"] = {}
    adicionar_estrelas(interaction.user.id, total)
    salvar_dados(dados)
    await interaction.response.send_message(embed=discord.Embed(title="💰 Vendeu tudo!", description="\n".join(lista) + f"\n\n**+{total} ⭐ | Saldo: {dados[uid]['estrelas']} ⭐**", color=0xFFD700))

@bot.tree.command(name="vender_minério_específico", description="Venda um minério específico")
@app_commands.describe(minerio="Qual minério", quantidade="Quanto (vazio = tudo desse)")
async def vender_minerio(interaction: discord.Interaction, minerio: str, quantidade: int = None):
    dados = carregar_dados()
    uid = str(interaction.user.id)
    info = next((m for m in MINERIOS if m["nome"].lower() == minerio.lower()), None)
    if not info or info["nome"] not in dados.get(uid, {}).get("minerios", {}):
        await interaction.response.send_message(f"❌ Você não tem {minerio}.", ephemeral=True)
        return
    tem = dados[uid]["minerios"][info["nome"]]
    qtd_vender = quantidade if quantidade and quantidade <= tem else tem
    ganho = info["valor"] * qtd_vender
    dados[uid]["minerios"][info["nome"]] -= qtd_vender
    if dados[uid]["minerios"][info["nome"]] <= 0: del dados[uid]["minerios"][info["nome"]]
    adicionar_estrelas(interaction.user.id, ganho)
    salvar_dados(dados)
    await interaction.response.send_message(f"💰 Vendeu **{qtd_vender}x {info['emoji']} {info['nome']}** por **{ganho} ⭐**! Saldo: {dados[uid]['estrelas']} ⭐")

@vender_minerio.autocomplete("minerio")
async def ac_vender(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=m["nome"], value=m["nome"]) for m in MINERIOS if current.lower() in m["nome"].lower()][:25]

@bot.tree.command(name="lojinha_de_picaretas", description="Evolua sua picareta")
async def loja(interaction: discord.Interaction):
    dados = carregar_dados()
    uid = str(interaction.user.id)
    lvl = dados.get(uid, {}).get("picareta", 1)
    estrelas = pegar_estrelas(interaction.user.id)
    embed = discord.Embed(title="🛒 Loja de Picaretas", description=f"Suas estrelas: **{estrelas} ⭐**\nAtual: **{PICARETAS[lvl]['nome']}**", color=0x2b2d31)
    for l, pic in PICARETAS.items():
        if l == 1: continue
        status = "✅ Já tem" if l <= lvl else f"💲 {pic['preco']} ⭐ - /comprar {pic['nome']}"
        embed.add_field(name=f"{pic['emoji']} {pic['nome']}", value=status, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="comprar_picareta", description="Compre uma picareta")
@app_commands.describe(picareta="Qual picareta")
async def comprar(interaction: discord.Interaction, picareta: str):
    dados = carregar_dados()
    uid = str(interaction.user.id)
    if uid not in dados:
        await interaction.response.send_message("Minere primeiro! /minerar", ephemeral=True)
        return
    alvo = next((lvl for lvl, p in PICARETAS.items() if p["nome"].lower() == picareta.lower()), None)
    if not alvo or alvo <= dados[uid]["picareta"]:
        await interaction.response.send_message("Você já tem essa!", ephemeral=True)
        return
    preco = PICARETAS[alvo]["preco"]
    if pegar_estrelas(interaction.user.id) < preco:
        await interaction.response.send_message(f"Precisa de {preco} ⭐, você tem {pegar_estrelas(interaction.user.id)} ⭐", ephemeral=True)
        return
    remover_estrelas(interaction.user.id, preco)
    dados[uid]["picareta"] = alvo
    salvar_dados(dados)
    await interaction.response.send_message(f"🎉 Comprou **{PICARETAS[alvo]['nome']}**!")
@comprar.autocomplete("picareta")
async def ac_comprar(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=p["nome"], value=p["nome"]) for p in PICARETAS.values() if current.lower() in p["nome"].lower()][:25]
    
bot.run(os.environ.get("DISCORD_TOKEN"))
