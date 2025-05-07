import discord
from discord.ext import commands
import os
import json
import datetime
from dotenv import load_dotenv
import random
import asyncio

# --- Carrega variáveis de ambiente ---
load_dotenv()

# --- Configurações do Bot ---
ACCOUNTS_FILE = "accounts.json"      # Arquivo que armazena as contas em formato JSON
CONFIG_FILE = "gen_bot_config.json"  # Arquivo de configuração
LOG_FILE = "gen_bot_log.txt"         # Arquivo de log

# --- Configuração do Bot ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Necessário para enviar DMs

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuração padrão
config = {
    "gen_channel_id": int(os.getenv("CHANNEL_ID", "0")),  # Carrega do .env
    "cooldown_minutes": 60,  # Tempo de espera entre gerações (em minutos)
    "admin_role_id": 0,      # ID do cargo de admin para adicionar contas
    "embed_color": 0x2F3136, # Cor padrão dos embeds (cinza escuro do Discord)
    "accent_color": 0x5865F2 # Cor de destaque (azul Discord)
}

# Cores para embeds (pode ser personalizado)
COLORS = {
    "success": 0x57F287,  # Verde
    "error": 0xED4245,    # Vermelho
    "warning": 0xFEE75C,  # Amarelo
    "info": 0x5865F2,     # Azul
    "purple": 0x9B59B6,   # Roxo
    "orange": 0xE67E22,   # Laranja
    "cyan": 0x1ABC9C,     # Ciano
    "pink": 0xFC3A82,     # Rosa
    # Cores específicas para serviços populares
    "valorant": 0xFD4553, # Vermelho Valorant
    "netflix": 0xE50914,  # Vermelho Netflix
    "spotify": 0x1DB954,  # Verde Spotify
    "hbo": 0x5822B4,      # Roxo HBO
    "disney": 0x113CCF,   # Azul Disney+
    "amazon": 0xFF9900    # Laranja Amazon
}

# Ícones para categorias específicas (emoji como identificador visual)
CATEGORY_ICONS = {
    "valorant": "🎮",
    "netflix": "🎬",
    "hbo": "🍿",
    "disney": "✨",
    "spotify": "🎵",
    "youtube": "▶️",
    "amazon": "📦",
    "steam": "🎲",
    "uplay": "🔫",
    "origin": "🎯",
    "crunchyroll": "🎌",
    "pornhub": "🔞",
    "minecraft": "⛏️",
    "facebook": "👤",
    "instagram": "📸",
    "twitter": "🐦",
    "default": "🔑"  # Ícone padrão para categorias não mapeadas
}

# Emojis para diferentes tipos de mensagens
EMOJIS = {
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
    "account": "🔑",
    "time": "⏳",
    "gen": "🎮",
    "admin": "👑",
    "stats": "📊",
    "config": "⚙️",
    "stock": "📋"
}

# Dicionário para controlar o cooldown dos usuários
user_cooldowns = {}

# --- Funções de Utilidade ---
def load_config():
    """Carrega a configuração do arquivo."""
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # Atualiza apenas as chaves existentes no config padrão
                for key in config:
                    if key in loaded_config:
                        config[key] = loaded_config[key]
            print(f"[CONFIG] Configuração carregada: {CONFIG_FILE}")
        else:
            save_config()
            print(f"[CONFIG] Arquivo de configuração não encontrado. Configuração padrão criada: {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao carregar configuração: {e}")

def save_config():
    """Salva a configuração no arquivo."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"[CONFIG] Configuração salva: {CONFIG_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao salvar configuração: {e}")

def load_accounts():
    """Carrega as contas do arquivo JSON."""
    accounts = {}
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                accounts = json.load(f)
            
            # Conta o total de contas
            total_accounts = sum(len(accs) for accs in accounts.values())
            print(f"[ACCOUNTS] {total_accounts} contas em {len(accounts)} categorias carregadas de {ACCOUNTS_FILE}")
        else:
            # Cria um arquivo JSON vazio com estrutura de dicionário
            with open(ACCOUNTS_FILE, 'w') as f:
                json.dump({}, f)
            print(f"[ACCOUNTS] Arquivo de contas não encontrado. Criando arquivo vazio: {ACCOUNTS_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao carregar contas: {e}")
        # Se houver erro, retorna um dicionário vazio
        accounts = {}
    return accounts

def save_accounts(accounts):
    """Salva as contas no arquivo JSON."""
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts, f, indent=4)
        
        # Conta o total de contas
        total_accounts = sum(len(accs) for accs in accounts.values())
        print(f"[ACCOUNTS] {total_accounts} contas em {len(accounts)} categorias salvas em {ACCOUNTS_FILE}")
    except Exception as e:
        print(f"[ERRO] Erro ao salvar contas: {e}")

def get_category_icon(category):
    """Retorna o ícone associado à categoria."""
    return CATEGORY_ICONS.get(category.lower(), CATEGORY_ICONS["default"])

def get_category_color(category):
    """Retorna a cor associada à categoria."""
    return COLORS.get(category.lower(), COLORS["info"])

def log_action(user, action, details=""):
    """Registra uma ação no arquivo de log."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {user} - {action} - {details}\n"
        
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[ERRO] Erro ao registrar log: {e}")

def create_embed(title, description, color_name="info", thumbnail=None, footer=None, image=None, fields=None):
    """Cria um embed estilizado para o Discord."""
    color = COLORS.get(color_name, config["embed_color"])
    
    # Adiciona emoji ao título se não tiver
    if title and not any(emoji in title for emoji in EMOJIS.values()):
        emoji = EMOJIS.get(color_name, EMOJIS["info"])
        title = f"{emoji} {title}"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.datetime.now()
    )
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if image:
        embed.set_image(url=image)
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False)
            )
    
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text=f"{bot.user.name} • Account Generator")
    
    return embed

def format_category_name(category):
    """Formata o nome da categoria para exibição."""
    # Primeira letra maiúscula, resto minúsculo
    return category.lower().capitalize()

# --- Eventos do Bot ---
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name} ({bot.user.id})')
    
    # Imprime o canal de geração configurado
    channel_id = config["gen_channel_id"]
    channel = bot.get_channel(channel_id)
    if channel:
        print(f'Canal de geração: #{channel.name} ({channel_id})')
    else:
        print(f'Canal de geração configurado: {channel_id} (não encontrado)')
    
    # Verifica e cria o arquivo de contas se não existir
    if not os.path.exists(ACCOUNTS_FILE):
        save_accounts({})
    
    print('------')
    
    # Define o status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="!gen [categoria] para uma conta"
        )
    )

# --- Comandos ---
@bot.command(name="gen")
async def generate_account(ctx, category=None):
    """Gera uma conta para o usuário de uma categoria específica."""
    # Verifica se o comando foi enviado no canal correto
    if ctx.channel.id != config["gen_channel_id"]:
        return
    
    # Verifica o cooldown do usuário
    user_id = str(ctx.author.id)
    current_time = datetime.datetime.now()
    
    if user_id in user_cooldowns:
        last_gen_time = user_cooldowns[user_id]
        time_diff = current_time - last_gen_time
        cooldown_minutes = config["cooldown_minutes"]
        
        if time_diff.total_seconds() < (cooldown_minutes * 60):
            remaining_minutes = cooldown_minutes - (time_diff.total_seconds() // 60)
            
            # Cria embed de erro de cooldown
            embed = create_embed(
                title="Cooldown Ativo",
                description=f"Você precisa esperar mais **{int(remaining_minutes)} minutos** para gerar outra conta!",
                color_name="warning",
                fields=[
                    {
                        "name": "Próxima geração disponível em",
                        "value": f"<t:{int((last_gen_time + datetime.timedelta(minutes=cooldown_minutes)).timestamp())}:R>"
                    }
                ]
            )
            
            error_msg = await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.delete(delay=10)  # Deleta o comando após 10 segundos
            await error_msg.delete(delay=10)  # Deleta a mensagem de erro após 10 segundos
            return
    
    # Carrega as contas
    accounts = load_accounts()
    
    # Se não foi especificada uma categoria
    if category is None:
        # Verifica se há alguma categoria disponível
        available_categories = [cat for cat, accs in accounts.items() if accs]
        
        if not available_categories:
            embed = create_embed(
                title="Sem Contas Disponíveis",
                description="Não há contas disponíveis no momento. Por favor, tente novamente mais tarde.",
                color_name="error"
            )
            error_msg = await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.delete(delay=10)
            await error_msg.delete(delay=10)
            return
        
        # Mensagem de erro para especificar categoria
        categories_text = ", ".join([f"`{cat}`" for cat in sorted(available_categories)])
        embed = create_embed(
            title="Categoria Necessária",
            description="Por favor, especifique uma categoria para gerar uma conta.",
            color_name="warning",
            fields=[
                {
                    "name": "Categorias Disponíveis",
                    "value": categories_text,
                    "inline": False
                },
                {
                    "name": "Exemplo de Uso",
                    "value": f"`!gen valorant`",
                    "inline": False
                }
            ]
        )
        
        error_msg = await ctx.reply(embed=embed, mention_author=False)
        await ctx.message.delete(delay=15)
        await error_msg.delete(delay=15)
        return
    
    # Normaliza o nome da categoria (minúsculo)
    category = category.lower()
    
    # Verifica se a categoria existe
    if category not in accounts or not accounts[category]:
        # Verifica se a categoria existe, mas está vazia
        if category in accounts:
            embed = create_embed(
                title=f"Sem Contas {format_category_name(category)}",
                description=f"Não há contas de {format_category_name(category)} disponíveis no momento.",
                color_name="error"
            )
        else:
            # A categoria não existe
            available_categories = [cat for cat, accs in accounts.items() if accs]
            categories_text = ", ".join([f"`{cat}`" for cat in sorted(available_categories)])
            
            embed = create_embed(
                title="Categoria Não Encontrada",
                description=f"A categoria `{category}` não existe ou está vazia.",
                color_name="error",
                fields=[
                    {
                        "name": "Categorias Disponíveis",
                        "value": categories_text if available_categories else "Nenhuma categoria disponível",
                        "inline": False
                    }
                ]
            )
        
        error_msg = await ctx.reply(embed=embed, mention_author=False)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Pega a primeira conta da categoria
    account = accounts[category][0]
    accounts[category].pop(0)  # Remove a conta da lista
    
    # Remove a categoria se ficou vazia
    if not accounts[category]:
        accounts[category] = []
    
    # Salva a lista atualizada
    save_accounts(accounts)
    
    # Atualiza o cooldown do usuário
    user_cooldowns[user_id] = current_time
    
    # Envia a conta por DM
    try:
        # Deleta o comando original
        await ctx.message.delete()
        
        # Calcula estatísticas
        total_accounts = sum(len(accs) for accs in accounts.values())
        category_remaining = len(accounts.get(category, []))
        
        # Cria embed de sucesso para o canal
        success_embed = create_embed(
            title=f"Conta {format_category_name(category)} Gerada",
            description=f"{ctx.author.mention} confira sua DM para ver os detalhes da conta!",
            color_name=category,
            fields=[
                {
                    "name": f"{get_category_icon(category)} Contas {format_category_name(category)} Restantes",
                    "value": f"{category_remaining}",
                    "inline": True
                },
                {
                    "name": "🔢 Total de Contas",
                    "value": f"{total_accounts}",
                    "inline": True
                },
                {
                    "name": "⏳ Próxima Geração",
                    "value": f"<t:{int((current_time + datetime.timedelta(minutes=config['cooldown_minutes'])).timestamp())}:R>",
                    "inline": True
                }
            ]
        )
        
        # Envia confirmação no canal
        confirmation = await ctx.send(embed=success_embed)
        
        # Prepara embed para DM
        account_parts = account.split(':')
        login = account_parts[0] if len(account_parts) > 0 else "N/A"
        password = account_parts[1] if len(account_parts) > 1 else "N/A"
        
        # Obter o ícone e a cor da categoria
        icon = get_category_icon(category)
        
        dm_embed = create_embed(
            title=f"{icon} Sua Conta {format_category_name(category)}",
            description="Aqui estão as informações da sua conta. Guarde-as em um local seguro!",
            color_name=category,
            fields=[
                {
                    "name": "📋 Login",
                    "value": f"```{login}```",
                    "inline": False
                },
                {
                    "name": "🔒 Senha",
                    "value": f"```{password}```",
                    "inline": False
                },
                {
                    "name": "🕒 Gerado em",
                    "value": f"<t:{int(current_time.timestamp())}:F>",
                    "inline": False
                },
                {
                    "name": "⚠️ Atenção",
                    "value": "Este login e senha são de uso único e não devem ser compartilhados.",
                    "inline": False
                }
            ]
        )
        
        # Adiciona o avatar do usuário ou do bot ao embed
        if ctx.author.avatar:
            dm_embed.set_thumbnail(url=ctx.author.avatar.url)
        elif bot.user.avatar:
            dm_embed.set_thumbnail(url=bot.user.avatar.url)
        
        # Envia a DM com a conta (sem autodestruição)
        await ctx.author.send(embed=dm_embed)
        
        # Registra no log
        total_remaining = sum(len(accs) for accs in accounts.values())
        log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", 
                  f"Gerou conta {category}", 
                  f"Restantes na categoria: {category_remaining}, Total: {total_remaining}")
        
        # Remove a confirmação após 15 segundos
        await confirmation.delete(delay=15)
        
    except discord.Forbidden:
        # Se não puder enviar DM (usuário bloqueou DMs)
        error_embed = create_embed(
            title="Erro ao Enviar Mensagem",
            description=f"{ctx.author.mention} não foi possível enviar a mensagem privada. Suas DMs estão abertas?",
            color_name="error",
            fields=[
                {
                    "name": "Como Habilitar DMs",
                    "value": "Clique direito no servidor → Configurações de Privacidade → Ative 'Permitir mensagens diretas de membros do servidor'",
                    "inline": False
                }
            ]
        )
        
        error_msg = await ctx.send(embed=error_embed)
        
        # Coloca a conta de volta na categoria
        if category not in accounts:
            accounts[category] = []
        accounts[category].insert(0, account)
        save_accounts(accounts)
        
        # Remove o cooldown
        if user_id in user_cooldowns:
            del user_cooldowns[user_id]
            
        # Remove a mensagem de erro após 15 segundos
        await error_msg.delete(delay=15)

@bot.command(name="addacc")
async def add_account(ctx, category=None, *, accounts_text=None):
    """Adiciona uma ou mais contas à categoria especificada."""
    # Verifica se o usuário tem permissão (admin ou dono do servidor)
    is_admin = False
    if ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id:
        is_admin = True
    elif config["admin_role_id"] != 0:
        role = ctx.guild.get_role(config["admin_role_id"])
        if role and role in ctx.author.roles:
            is_admin = True
    
    if not is_admin:
        error_embed = create_embed(
            title="Permissão Negada",
            description="Você não tem permissão para usar este comando.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=5)
        await error_msg.delete(delay=5)
        return
    
    # Verifica se a categoria foi fornecida
    if category is None:
        error_embed = create_embed(
            title="Categoria Necessária",
            description="Por favor, especifique uma categoria para adicionar contas.",
            color_name="error",
            fields=[
                {
                    "name": "Formato Correto",
                    "value": "```!addacc [categoria] [contas]```",
                    "inline": False
                },
                {
                    "name": "Exemplo",
                    "value": "```!addacc valorant\nlogin1:senha1\nlogin2:senha2```",
                    "inline": False
                }
            ]
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Verifica se as contas foram fornecidas
    if accounts_text is None:
        error_embed = create_embed(
            title="Contas Necessárias",
            description="Por favor, forneça as contas a serem adicionadas.",
            color_name="error",
            fields=[
                {
                    "name": "Formato Correto",
                    "value": "```!addacc [categoria]\nlogin1:senha1\nlogin2:senha2```",
                    "inline": False
                }
            ]
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Deleta o comando original para proteger as contas
    await ctx.message.delete()
    
    # Normaliza o nome da categoria (minúsculo)
    category = category.lower()
    
    # Processa as contas
    new_accounts = [line.strip() for line in accounts_text.split('\n') if line.strip() and ':' in line]
    
    if not new_accounts:
        error_embed = create_embed(
            title="Formato Inválido",
            description="Nenhuma conta válida encontrada. Use o formato `login:senha`.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await error_msg.delete(delay=10)
        return
    
    # Carrega as contas existentes
    accounts = load_accounts()
    
    # Adiciona a categoria se não existir
    if category not in accounts:
        accounts[category] = []
    
    # Adiciona as novas contas à categoria
    accounts[category].extend(new_accounts)
    
    # Salva todas as contas
    save_accounts(accounts)
    
    # Conta o total de contas
    total_accounts = sum(len(accs) for accs in accounts.values())
    category_total = len(accounts[category])
    
    # Envia confirmação
    success_embed = create_embed(
        title=f"Contas {format_category_name(category)} Adicionadas",
        description=f"{len(new_accounts)} contas de {format_category_name(category)} adicionadas com sucesso!",
        color_name=category,
        fields=[
            {
                "name": f"{get_category_icon(category)} Total na Categoria",
                "value": f"{category_total}",
                "inline": True
            },
            {
                "name": "🔢 Total Geral",
                "value": f"{total_accounts}",
                "inline": True
            },
            {
                "name": "👤 Adicionadas por",
                "value": f"{ctx.author.mention}",
                "inline": True
            }
        ]
    )
    
    confirmation = await ctx.send(embed=success_embed)
    await confirmation.delete(delay=10)
    
    # Registra no log
    log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", 
              f"Adicionou contas {category}", 
              f"Quantidade: {len(new_accounts)}, Total na categoria: {category_total}, Total geral: {total_accounts}")

@bot.command(name="stock")
async def check_stock(ctx):
    """Mostra o estoque de contas disponíveis por categoria."""
    # Verifica se o comando foi enviado no canal correto
    if ctx.channel.id != config["gen_channel_id"]:
        return
    
    # Carrega as contas
    accounts = load_accounts()
    
    # Verifica se há contas disponíveis
    if not accounts or all(len(accs) == 0 for accs in accounts.values()):
        embed = create_embed(
            title="Estoque Vazio",
            description="Não há contas disponíveis no momento.",
            color_name="warning"
        )
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete(delay=10)
        return
    
    # Filtra apenas categorias não vazias e ordena por nome
    categories = {cat: accs for cat, accs in accounts.items() if accs}
    sorted_categories = sorted(categories.keys())
    
    # Calcula o total de contas
    total_accounts = sum(len(accs) for accs in accounts.values())
    
    # Cria o embed base
    stock_embed = create_embed(
        title="Estoque de Contas",
        description=f"Temos um total de **{total_accounts}** contas disponíveis em **{len(categories)}** categorias.",
        color_name="stock"
    )
    
    # Adiciona campos para cada categoria com ícones e cores personalizadas
    for category in sorted_categories:
        category_icon = get_category_icon(category)
        category_count = len(accounts[category])
        
        # Adiciona o campo da categoria
        stock_embed.add_field(
            name=f"{category_icon} {format_category_name(category)}",
            value=f"**{category_count}** contas disponíveis\n`!gen {category}`",
            inline=True
        )
    
    # Adiciona informações de cooldown
    if config["cooldown_minutes"] > 0:
        stock_embed.add_field(
            name=f"{EMOJIS['time']} Tempo de Espera",
            value=f"**{config['cooldown_minutes']}** minutos entre gerações",
            inline=False
        )
    
    # Se o bot tiver um avatar, usa como thumbnail
    if bot.user.avatar:
        stock_embed.set_thumbnail(url=bot.user.avatar.url)
    
    # Adiciona timestamp dinâmico no footer
    stock_embed.set_footer(text=f"{bot.user.name} • Atualizado")
    
    # Envia o embed de estoque
    await ctx.send(embed=stock_embed)
    await ctx.message.delete()
    
    # Registra no log
    log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", 
              "Consultou estoque", 
              f"Total de contas: {total_accounts}")

@bot.command(name="remaining")
async def remaining_accounts(ctx):
    """Alias para o comando !stock, mantido para compatibilidade"""
    await check_stock(ctx)

@bot.command(name="setchannel")
async def set_channel(ctx, channel_id: int = None):
    """Define o canal onde o comando !gen funcionará."""
    # Verifica se o usuário é admin ou dono do servidor
    if not (ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id):
        error_embed = create_embed(
            title="Permissão Negada",
            description="Apenas administradores podem usar este comando.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=5)
        await error_msg.delete(delay=5)
        return
    
    # Se não foi fornecido um ID, usa o canal atual
    if channel_id is None:
        channel_id = ctx.channel.id
    
    # Verifica se o canal existe
    channel = bot.get_channel(channel_id)
    if not channel:
        error_embed = create_embed(
            title="Canal Não Encontrado",
            description=f"Canal com ID {channel_id} não encontrado.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Atualiza a configuração
    config["gen_channel_id"] = channel_id
    save_config()
    
    # Envia confirmação
    success_embed = create_embed(
        title="Canal Atualizado",
        description=f"Canal de geração definido para {channel.mention}.",
        color_name="config",
        fields=[
            {
                "name": "ID do Canal",
                "value": f"`{channel_id}`",
                "inline": True
            },
            {
                "name": "Alterado por",
                "value": f"{ctx.author.mention}",
                "inline": True
            }
        ]
    )
    
    await ctx.send(embed=success_embed, delete_after=15)
    await ctx.message.delete(delay=15)
    
    # Registra no log
    log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", "Alterou canal", f"Novo canal: {channel_id}")

@bot.command(name="setcooldown")
async def set_cooldown(ctx, minutes: int):
    """Define o tempo de cooldown entre gerações de contas."""
    # Verifica se o usuário é admin ou dono do servidor
    if not (ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id):
        error_embed = create_embed(
            title="Permissão Negada",
            description="Apenas administradores podem usar este comando.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=5)
        await error_msg.delete(delay=5)
        return
    
    # Verifica se o valor é válido
    if minutes < 0:
        error_embed = create_embed(
            title="Valor Inválido",
            description="O cooldown não pode ser negativo.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Atualiza a configuração
    config["cooldown_minutes"] = minutes
    save_config()
    
    # Texto personalizado para o cooldown
    cooldown_text = f"{minutes} minutos" if minutes > 0 else "desativado"
    
    # Envia confirmação
    success_embed = create_embed(
        title="Cooldown Atualizado",
        description=f"Cooldown definido para **{cooldown_text}**.",
        color_name="config",
        fields=[
            {
                "name": "Valor Anterior",
                "value": f"{config.get('cooldown_minutes', 60)} minutos",
                "inline": True
            },
            {
                "name": "Alterado por",
                "value": f"{ctx.author.mention}",
                "inline": True
            }
        ]
    )
    
    await ctx.send(embed=success_embed, delete_after=15)
    await ctx.message.delete(delay=15)
    
    # Registra no log
    log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", "Alterou cooldown", f"Novo cooldown: {minutes} minutos")

@bot.command(name="setadmin")
async def set_admin_role(ctx, role_id: int):
    """Define o cargo que terá permissões de admin no bot."""
    # Verifica se o usuário é o dono do servidor
    if ctx.author.id != ctx.guild.owner_id:
        error_embed = create_embed(
            title="Permissão Negada",
            description="Apenas o dono do servidor pode usar este comando.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=5)
        await error_msg.delete(delay=5)
        return
    
    # Verifica se o cargo existe
    role = ctx.guild.get_role(role_id)
    if not role:
        error_embed = create_embed(
            title="Cargo Não Encontrado",
            description=f"Cargo com ID {role_id} não encontrado.",
            color_name="error"
        )
        error_msg = await ctx.send(embed=error_embed)
        await ctx.message.delete(delay=10)
        await error_msg.delete(delay=10)
        return
    
    # Atualiza a configuração
    config["admin_role_id"] = role_id
    save_config()
    
    # Envia confirmação
    success_embed = create_embed(
        title="Cargo Admin Atualizado",
        description=f"Cargo admin definido para {role.mention}.",
        color_name="config",
        fields=[
            {
                "name": "ID do Cargo",
                "value": f"`{role_id}`",
                "inline": True
            },
            {
                "name": "Alterado por",
                "value": f"{ctx.author.mention}",
                "inline": True
            }
        ]
    )
    
    await ctx.send(embed=success_embed, delete_after=15)
    await ctx.message.delete(delay=15)
    
    # Registra no log
    log_action(f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})", "Alterou cargo admin", f"Novo cargo: {role_id}")

@bot.command(name="commands")
async def command_help(ctx):
    """Mostra informações de ajuda sobre os comandos do bot."""
    # Determina se o usuário é administrador
    is_admin = False
    if ctx.author.guild_permissions.administrator or ctx.author.id == ctx.guild.owner_id:
        is_admin = True
    elif config["admin_role_id"] != 0:
        role = ctx.guild.get_role(config["admin_role_id"])
        if role and role in ctx.author.roles:
            is_admin = True
    
    # Comandos para usuários normais
    user_commands = [
        {
            "name": "!gen [categoria]",
            "value": "Gera uma conta da categoria especificada e envia por DM",
            "inline": False
        },
        {
            "name": "!stock",
            "value": "Mostra as categorias e quantidades de contas disponíveis",
            "inline": False
        },
        {
            "name": "!commands",
            "value": "Mostra esta mensagem de ajuda",
            "inline": False
        }
    ]
    
    # Comandos adicionais para administradores
    admin_commands = [
        {
            "name": "!addacc [categoria]",
            "value": "Adiciona contas à categoria especificada (formato: login:senha)",
            "inline": False
        },
        {
            "name": "!setchannel [ID]",
            "value": "Define o canal para geração de contas (usa o canal atual se não especificado)",
            "inline": False
        },
        {
            "name": "!setcooldown [min]",
            "value": "Define o tempo de espera em minutos entre gerações",
            "inline": False
        },
        {
            "name": "!setadmin [ID]",
            "value": "Define o cargo com permissões admin",
            "inline": False
        }
    ]
    
    # Carrega as contas para mostrar categorias disponíveis
    accounts = load_accounts()
    available_categories = sorted([cat for cat, accs in accounts.items() if accs])
    
    # Cria o embed de ajuda
    help_embed = create_embed(
        title="Comandos do Gerador de Contas",
        description="Abaixo estão os comandos disponíveis para você:",
        color_name="info"
    )
    
    # Adiciona os comandos de usuário
    for cmd in user_commands:
        help_embed.add_field(
            name=cmd["name"],
            value=cmd["value"],
            inline=cmd["inline"]
        )
    
    # Adiciona categorias disponíveis
    if available_categories:
        categories_text = ", ".join([f"`{cat}`" for cat in available_categories])
        help_embed.add_field(
            name="📋 Categorias Disponíveis",
            value=categories_text,
            inline=False
        )
    
    # Adiciona comandos de admin se o usuário for admin
    if is_admin:
        help_embed.add_field(
            name="⚙️ Comandos de Administração",
            value="Comandos disponíveis apenas para administradores:",
            inline=False
        )
        
        for cmd in admin_commands:
            help_embed.add_field(
                name=cmd["name"],
                value=cmd["value"],
                inline=cmd["inline"]
            )
    
    # Adiciona informações de cooldown
    if config["cooldown_minutes"] > 0:
        help_embed.add_field(
            name="⏳ Cooldown Atual",
            value=f"{config['cooldown_minutes']} minutos entre gerações",
            inline=False
        )
    
    # Adiciona o canal atual
    channel = bot.get_channel(config["gen_channel_id"])
    if channel:
        help_embed.add_field(
            name="📌 Canal de Geração",
            value=f"{channel.mention}",
            inline=False
        )
    
    # Adiciona avatar do bot no embed
    if bot.user.avatar:
        help_embed.set_thumbnail(url=bot.user.avatar.url)
    
    # Envia a mensagem
    await ctx.send(embed=help_embed, delete_after=30)
    await ctx.message.delete(delay=30)

# --- Manipulador de erros para comandos ---
@bot.event
async def on_command_error(ctx, error):
    """Manipula erros de comando."""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignora comandos não encontrados
    
    if isinstance(error, commands.MissingRequiredArgument):
        # Argumentos faltando
        param_name = error.param.name
        if ctx.command.name == "addacc" and param_name == "category":
            # Erro específico para !addacc sem categoria
            error_embed = create_embed(
                title="Categoria Necessária",
                description="Por favor, especifique uma categoria.",
                color_name="error",
                fields=[
                    {
                        "name": "Formato Correto",
                        "value": "```!addacc [categoria]\nlogin1:senha1\nlogin2:senha2```",
                        "inline": False
                    }
                ]
            )
        elif ctx.command.name == "gen" and param_name == "category":
            # Erro específico para !gen sem categoria
            accounts = load_accounts()
            available_categories = sorted([cat for cat, accs in accounts.items() if accs])
            
            if not available_categories:
                error_embed = create_embed(
                    title="Sem Contas Disponíveis",
                    description="Não há contas disponíveis no momento.",
                    color_name="error"
                )
            else:
                categories_text = ", ".join([f"`{cat}`" for cat in available_categories])
                error_embed = create_embed(
                    title="Categoria Necessária",
                    description="Por favor, especifique uma categoria para gerar uma conta.",
                    color_name="warning",
                    fields=[
                        {
                            "name": "Categorias Disponíveis",
                            "value": categories_text,
                            "inline": False
                        }
                    ]
                )
        else:
            # Erro genérico para outros comandos
            error_embed = create_embed(
                title="Comando Incompleto",
                description=f"Faltando o parâmetro `{param_name}`.",
                color_name="error",
                fields=[
                    {
                        "name": "Uso Correto",
                        "value": f"Digite `!commands` para ver o uso correto.",
                        "inline": False
                    }
                ]
            )
        
        await ctx.send(embed=error_embed, delete_after=10)
        await ctx.message.delete(delay=10)
        return
    
    # Outros erros (para depuração)
    print(f"[ERRO] {ctx.command} - {error}")

# --- Bloco principal ---
if __name__ == "__main__":
    # Carrega a configuração
    load_config()
    
    # Obtém o token do ambiente
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        print("[ERRO] Token não configurado no arquivo .env")
        exit(1)
    
    # Inicia o bot
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("[ERRO] Token inválido. Verifique o token e tente novamente.")
    except Exception as e:
        print(f"[ERRO] Erro ao iniciar o bot: {e}")