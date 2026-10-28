import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional

# ==================== CONFIG ====================
BOT_TOKEN = "MTU2NDY4NDAzMTQzNjY1MjcyNA.G2isVK.yxkDKSahwdNY1O0vRDpBhFx1xiX9AW0--5XTTQ"
GUILD_ID = 1560361262288736407

LOG_CHANNEL_ID = 1564028184578621501
TICKET_CATEGORY_ID = 1564024009337864223
WELCOME_CHANNEL_ID = 1564723209004261477
VOUCH_CHANNEL_ID = 1564700606512234556

FREE_GEN_ROLE_ID = 1564689122076139601
PREMIUM_ROLE_ID = 1564689723526750318
BYPASS_ROLE_ID = 1564688522982723634
STAFF_ROLE_ID = 1564690303741464637

BASE_COOLDOWN_HRS = 3

# Banner links
TICKET_BANNER = "https://cdn.discordapp.com/attachments/1564028184578621501/1564716350633414798/Gemini_Generated_Image_gauv5cgauv5cgauv.jfif?ex=6ae24729&is=6ae0f5a9&hm=bff3347f20eef5c43178cedb46a5b576653cbd6b1e33301d407ab55693e5f359&"
GEN_BANNER = "https://cdn.discordapp.com/attachments/1564028184578621501/1564716385777619285/633fd1b3c94035c5033b6ad180a17529.jpg?ex=6ae24731&is=6ae0f5b1&hm=936846a3016ab24e0f53e299f389dacbe811a896bca17a3baca516853c394cff&"
WELCOME_BANNER = "https://cdn.discordapp.com/attachments/1564028184578621501/1564724742462640139/5f5c6ec9afe023fa8854b0fe357255cd.jpg?ex=6ae24ef9&is=6ae0fd79&hm=06a5b9d7225b29f24a8f7e7b8d707fe2915779576cd87ef15609ce2dc3970534&"
STOCK_BANNER = "https://cdn.discordapp.com/attachments/1564028184578621501/1564716350633414798/Gemini_Generated_Image_gauv5cgauv5cgauv.jfif?ex=6ae24729&is=6ae0f5a9&hm=bff3347f20eef5c43178cedb46a5b576653cbd6b1e33301d407ab55693e5f359&"

STOCK_FILE = "stock.json"
COOLDOWN_FILE = "cooldowns.json"
USED_FILE = "used_accounts.json"

# Custom Emojis
EMOJI_ROBLOX = discord.PartialEmoji(name="roblox", id=1522573796152705054)
EMOJI_FORTNITE = discord.PartialEmoji(name="fortnite", id=1542994905285132398)
EMOJI_NETFLIX = discord.PartialEmoji(name="netflix", id=1522572491451793459)
EMOJI_CRUNCHYROLL = discord.PartialEmoji(name="crunchyroll", id=1522572348434284647)
EMOJI_DISCORD = discord.PartialEmoji(name="discord", id=1346959177330720849)
# =================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- helpers ----------
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_stock():
    return load_json(STOCK_FILE, {
        "roblox": [],
        "fortnite": [],
        "netflix": [],
        "crunchyroll": [],
        "discord": []
    })

def save_stock(data):
    save_json(STOCK_FILE, data)

def get_cooldown(user_id: int) -> Optional[datetime]:
    data = load_json(COOLDOWN_FILE, {})
    ts = data.get(str(user_id))
    if ts:
        return datetime.fromisoformat(ts)
    return None

def set_cooldown(user_id: int):
    data = load_json(COOLDOWN_FILE, {})
    data[str(user_id)] = (datetime.utcnow() + timedelta(hours=BASE_COOLDOWN_HRS)).isoformat()
    save_json(COOLDOWN_FILE, data)

def is_used(account: str) -> bool:
    used = load_json(USED_FILE, [])
    return account in used

def mark_used(account: str):
    used = load_json(USED_FILE, [])
    if account not in used:
        used.append(account)
        save_json(USED_FILE, used)

def has_gen_access(member: discord.Member) -> bool:
    role_ids = [r.id for r in member.roles]
    return FREE_GEN_ROLE_ID in role_ids or PREMIUM_ROLE_ID in role_ids

def has_bypass(member: discord.Member) -> bool:
    return BYPASS_ROLE_ID in [r.id for r in member.roles]

def is_staff(member: discord.Member) -> bool:
    return STAFF_ROLE_ID in [r.id for r in member.roles] or member.guild_permissions.administrator

# ---------- WELCOME ----------
@bot.event
async def on_member_join(member: discord.Member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    embed = discord.Embed(
        title="❄️ Welcome to Icy Gen",
        description=f"Hey {member.mention}, welcome to the server!\n\nMake sure to read the rules and grab your roles.",
        color=0x00ccff
    )
    embed.set_image(url=WELCOME_BANNER)
    embed.set_footer(text="icy gen")
    embed.set_thumbnail(url=member.display_avatar.url)

    await channel.send(content=member.mention, embed=embed)

# ---------- STATUS ROLE (discord.gg/icygen) ----------
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    if after.guild is None or after.guild.id != GUILD_ID:
        return

    target_role = after.guild.get_role(FREE_GEN_ROLE_ID)
    if not target_role:
        return

    has_invite = False
    for activity in after.activities:
        if isinstance(activity, discord.CustomActivity):
            if activity.name and "discord.gg/icygen" in activity.name.lower():
                has_invite = True
                break

    try:
        if has_invite:
            if target_role not in after.roles:
                await after.add_roles(target_role, reason="Has discord.gg/icygen in status")
        else:
            if target_role in after.roles:
                await after.remove_roles(target_role, reason="Removed discord.gg/icygen from status")
    except:
        pass

# ---------- TICKET SYSTEM ----------
class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Payment", description="Payment related issues", emoji="💳", value="payment"),
            discord.SelectOption(label="Order Issue", description="Problems with your order", emoji="📦", value="order"),
            discord.SelectOption(label="Feedback", description="Send feedback or suggestions", emoji="💬", value="feedback"),
            discord.SelectOption(label="Other", description="Any other question", emoji="❓", value="other"),
        ]
        super().__init__(placeholder="Select a ticket type...", options=options, custom_id="ticket_select")

    async def callback(self, interaction: discord.Interaction):
        category_map = {
            "payment": ("Payment", "💳"),
            "order": ("Order Issue", "📦"),
            "feedback": ("Feedback", "💬"),
            "other": ("Other", "❓")
        }
        cat, emoji = category_map[self.values[0]]
        await create_ticket(interaction, cat, emoji)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

async def create_ticket(interaction: discord.Interaction, category: str, emoji: str):
    guild = interaction.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
    }
    name = f"ticket-{interaction.user.name}-{category.lower().replace(' ', '-')}"[:90]
    channel = await guild.create_text_channel(
        name=name,
        category=guild.get_channel(TICKET_CATEGORY_ID),
        overwrites=overwrites,
        reason=f"Ticket by {interaction.user}"
    )
    embed = discord.Embed(
        title=f"{emoji} {category} Ticket",
        description=f"Hello {interaction.user.mention},\nStaff will assist you shortly.\n\n**Category:** {category}",
        color=0x00ccff
    )
    embed.set_footer(text="icy gen • ticket system")
    close_view = CloseTicketView()
    await channel.send(content=f"{interaction.user.mention} | <@&{STAFF_ROLE_ID}>", embed=embed, view=close_view)
    await interaction.response.send_message(f"✅ Ticket created → {channel.mention}", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("Only staff can close tickets.", ephemeral=True)
        await interaction.response.send_message("Closing in 3 seconds...")
        await asyncio.sleep(3)
        await interaction.channel.delete(reason=f"Closed by {interaction.user}")

# ---------- GEN SYSTEM ----------
class GenSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Roblox Accounts", description="Generate a Roblox account", emoji=EMOJI_ROBLOX, value="roblox"),
            discord.SelectOption(label="Fortnite Accounts", description="Generate a Fortnite account", emoji=EMOJI_FORTNITE, value="fortnite"),
            discord.SelectOption(label="Netflix Accounts", description="Generate a Netflix account", emoji=EMOJI_NETFLIX, value="netflix"),
            discord.SelectOption(label="Crunchyroll Accounts", description="Generate a Crunchyroll account", emoji=EMOJI_CRUNCHYROLL, value="crunchyroll"),
            discord.SelectOption(label="Discord Accounts", description="Generate a Discord account", emoji=EMOJI_DISCORD, value="discord"),
        ]
        super().__init__(placeholder="Select a service to generate...", options=options, custom_id="gen_select")

    async def callback(self, interaction: discord.Interaction):
        service = self.values[0]
        await handle_gen(interaction, service)

class GenView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GenSelect())

async def handle_gen(interaction: discord.Interaction, service: str):
    user = interaction.user
    member = interaction.guild.get_member(user.id)

    if not has_gen_access(member):
        return await interaction.response.send_message("❌ You need Free Gen or Premium role to generate.", ephemeral=True)

    if not has_bypass(member):
        cd = get_cooldown(user.id)
        if cd and datetime.utcnow() < cd:
            remaining = cd - datetime.utcnow()
            hours, rem = divmod(int(remaining.total_seconds()), 3600)
            mins = rem // 60
            return await interaction.response.send_message(
                f"⏳ Cooldown active. Try again in **{hours}h {mins}m**.", ephemeral=True
            )

    data = get_stock()
    stock = [a for a in data.get(service, []) if not is_used(a["account"])]
    
    if not stock:
        return await interaction.response.send_message(f"❌ **{service.title()}** stock is empty right now.", ephemeral=True)

    item = stock.pop(0)
    account = item["account"]
    note = item.get("note", "")

    data[service] = [a for a in data[service] if a["account"] != account]
    save_stock(data)
    mark_used(account)

    if not has_bypass(member):
        set_cooldown(user.id)

    try:
        desc = f"```{account}```"
        if note:
            desc += f"\n**Note:** {note}"

        embed = discord.Embed(
            title=f"❄️ {service.title()} Account Generated",
            description=desc,
            color=0x00ffcc
        )
        embed.set_footer(text="icy gen • do not share")
        await user.send(embed=embed)
        await interaction.response.send_message(f"✅ **{service.title()}** account sent to your DMs!", ephemeral=True)
    except discord.Forbidden:
        data[service].insert(0, item)
        save_stock(data)
        return await interaction.response.send_message("❌ I couldn't DM you. Open your DMs and try again.", ephemeral=True)

    log_ch = interaction.guild.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        log_embed = discord.Embed(
            title="🧾 Account Generated",
            color=0x00ccff,
            timestamp=datetime.utcnow()
        )
        log_embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=False)
        log_embed.add_field(name="Service", value=service.title(), inline=True)
        log_embed.add_field(name="Account", value=f"```{account}```", inline=False)
        if note:
            log_embed.add_field(name="Note", value=note, inline=False)
        log_embed.add_field(name="Remaining", value=str(len(data[service])), inline=True)
        await log_ch.send(embed=log_embed)

# ---------- STOCK VIEWER ----------
class StockViewSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Roblox", emoji=EMOJI_ROBLOX, value="roblox"),
            discord.SelectOption(label="Fortnite", emoji=EMOJI_FORTNITE, value="fortnite"),
            discord.SelectOption(label="Netflix", emoji=EMOJI_NETFLIX, value="netflix"),
            discord.SelectOption(label="Crunchyroll", emoji=EMOJI_CRUNCHYROLL, value="crunchyroll"),
            discord.SelectOption(label="Discord", emoji=EMOJI_DISCORD, value="discord"),
        ]
        super().__init__(placeholder="Select a service to check stock...", options=options, custom_id="stock_view_select")

    async def callback(self, interaction: discord.Interaction):
        service = self.values[0]
        data = get_stock()
        count = len([a for a in data.get(service, []) if not is_used(a["account"])])
        embed = discord.Embed(
            title=f"📦 {service.title()} Stock",
            description=f"**Available:** `{count}`",
            color=0x00ccff
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class StockView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(StockViewSelect())

# ---------- COMMANDS ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)
    bot.add_view(TicketView())
    bot.add_view(GenView())
    bot.add_view(CloseTicketView())
    bot.add_view(StockView())

@bot.tree.command(name="ticketpanel", description="Send the ticket panel", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def ticketpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❄️ Icy Gen • Ticket System",
        description="If you need help or have any issues, select a ticket type from the dropdown menu below.\n\n• **Reminder**\nWe are not online 24/7 so please be patient.",
        color=0x00ccff
    )
    embed.set_image(url=TICKET_BANNER)
    embed.set_footer(text="icy gen • support")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Ticket panel sent.", ephemeral=True)

@bot.tree.command(name="genpanel", description="Send the gen panel", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def genpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="❄️ Icy Gen • Account Generator",
        description=(
            "**Services**\n"
            "Choose from Roblox, Fortnite, Netflix, Crunchyroll & Discord accounts.\n\n"
            "**Premium Advantages**\n"
            "Users with Premium enjoy lower cooldowns and priority support.\n\n"
            f"**Cooldown**\n"
            f"{BASE_COOLDOWN_HRS} hours (Bypass role skips it)"
        ),
        color=0x00ccff
    )
    embed.set_image(url=GEN_BANNER)
    embed.set_footer(text="icy gen • generate")
    await interaction.channel.send(embed=embed, view=GenView())
    await interaction.response.send_message("Gen panel sent.", ephemeral=True)

@bot.tree.command(name="stockpanel", description="Send the public stock viewer", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def stockpanel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📦 Icy Gen • Stock Viewer",
        description="Select a service below to check current available stock.",
        color=0x00ccff
    )
    embed.set_image(url=STOCK_BANNER)
    await interaction.channel.send(embed=embed, view=StockView())
    await interaction.response.send_message("Stock panel sent.", ephemeral=True)

@bot.tree.command(name="addstock", description="Add accounts to stock (staff only) - supports multiple", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    service="Which service",
    accounts="Paste accounts here (one per line)",
    note="Optional note that applies to all accounts"
)
@app_commands.choices(service=[
    app_commands.Choice(name="Roblox", value="roblox"),
    app_commands.Choice(name="Fortnite", value="fortnite"),
    app_commands.Choice(name="Netflix", value="netflix"),
    app_commands.Choice(name="Crunchyroll", value="crunchyroll"),
    app_commands.Choice(name="Discord", value="discord"),
])
async def addstock(interaction: discord.Interaction, service: str, accounts: str, note: str = None):
    if not is_staff(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    lines = [line.strip() for line in accounts.splitlines() if line.strip()]
    
    if not lines:
        return await interaction.response.send_message("No accounts detected.", ephemeral=True)

    data = get_stock()
    added = 0

    for acc in lines:
        data[service].append({
            "account": acc,
            "note": note.strip() if note else ""
        })
        added += 1

    save_stock(data)

    await interaction.response.send_message(
        f"✅ Successfully added **{added}** accounts to **{service.title()}**!"
        + (f"\nNote applied: `{note}`" if note else ""),
        ephemeral=True
    )

@bot.tree.command(name="removestock", description="Remove accounts from stock (staff only)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    service="Which service",
    accounts="Type 'view' to see current stock, or paste accounts to remove (one per line)"
)
@app_commands.choices(service=[
    app_commands.Choice(name="Roblox", value="roblox"),
    app_commands.Choice(name="Fortnite", value="fortnite"),
    app_commands.Choice(name="Netflix", value="netflix"),
    app_commands.Choice(name="Crunchyroll", value="crunchyroll"),
    app_commands.Choice(name="Discord", value="discord"),
])
async def removestock(interaction: discord.Interaction, service: str, accounts: str):
    if not is_staff(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    data = get_stock()
    current = data.get(service, [])

    # If user types "view" → show current stock
    if accounts.lower().strip() in ["view", "list", "show"]:
        if not current:
            return await interaction.response.send_message(f"**{service.title()}** stock is empty.", ephemeral=True)

        lines = [f"`{i+1}.` {item['account']}" for i, item in enumerate(current)]
        text = "\n".join(lines)

        if len(text) > 4000:
            text = text[:4000] + "\n... (too many accounts to display)"

        embed = discord.Embed(
            title=f"📦 {service.title()} Stock ({len(current)})",
            description=text,
            color=0x00ccff
        )
        embed.set_footer(text="Copy the accounts you want to remove and run the command again")
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    # Otherwise remove the given accounts
    to_remove = [line.strip() for line in accounts.splitlines() if line.strip()]
    
    if not to_remove:
        return await interaction.response.send_message("No accounts detected. Type `view` to see the list.", ephemeral=True)

    original = len(current)
    data[service] = [item for item in current if item["account"] not in to_remove]
    removed = original - len(data[service])
    
    save_stock(data)

    await interaction.response.send_message(
        f"✅ Removed **{removed}** accounts from **{service.title()}**.\nRemaining: **{len(data[service])}**",
        ephemeral=True
    )

@bot.tree.command(name="stock", description="Check stock (staff)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(service="Which service")
@app_commands.choices(service=[
    app_commands.Choice(name="Roblox", value="roblox"),
    app_commands.Choice(name="Fortnite", value="fortnite"),
    app_commands.Choice(name="Netflix", value="netflix"),
    app_commands.Choice(name="Crunchyroll", value="crunchyroll"),
    app_commands.Choice(name="Discord", value="discord"),
    app_commands.Choice(name="All", value="all"),
])
async def stock(interaction: discord.Interaction, service: str):
    if not is_staff(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    data = get_stock()
    if service == "all":
        msg = ""
        for s in data:
            count = len([a for a in data[s] if not is_used(a["account"])])
            msg += f"**{s.title()}:** `{count}`\n"
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        count = len([a for a in data.get(service, []) if not is_used(a["account"])])
        await interaction.response.send_message(f"**{service.title()}** stock: `{count}`", ephemeral=True)

@bot.tree.command(name="close", description="Close the current ticket", guild=discord.Object(id=GUILD_ID))
async def close(interaction: discord.Interaction):
    if not interaction.channel.name.startswith("ticket-"):
        return await interaction.response.send_message("This command can only be used in a ticket.", ephemeral=True)

    if not is_staff(interaction.user) and interaction.user not in interaction.channel.members:
        return await interaction.response.send_message("You can't close this ticket.", ephemeral=True)

    await interaction.response.send_message("🔒 Closing ticket in 3 seconds...")
    await asyncio.sleep(3)
    await interaction.channel.delete(reason=f"Closed by {interaction.user}")

@bot.tree.command(name="vouch", description="Leave a vouch", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    stars="Rating from 1 to 5",
    comment="Your vouch comment",
    image="Optional picture of what you got (attach an image)"
)
@app_commands.choices(stars=[
    app_commands.Choice(name="⭐ 1 Star", value=1),
    app_commands.Choice(name="⭐⭐ 2 Stars", value=2),
    app_commands.Choice(name="⭐⭐⭐ 3 Stars", value=3),
    app_commands.Choice(name="⭐⭐⭐⭐ 4 Stars", value=4),
    app_commands.Choice(name="⭐⭐⭐⭐⭐ 5 Stars", value=5),
])
async def vouch(interaction: discord.Interaction, stars: int, comment: str, image: discord.Attachment = None):
    vouch_channel = bot.get_channel(VOUCH_CHANNEL_ID)
    if not vouch_channel:
        return await interaction.response.send_message("Vouch channel not found.", ephemeral=True)

    stars_display = "⭐" * stars + "☆" * (5 - stars)

    embed = discord.Embed(
        title="❄️ New Vouch",
        description=f"**Rating:** {stars_display}\n\n**Comment:**\n{comment}",
        color=0x00ccff,
        timestamp=datetime.utcnow()
    )
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.display_avatar.url)
    embed.set_footer(text="icy gen • vouch system")

    if image:
        if image.content_type and image.content_type.startswith("image/"):
            embed.set_image(url=image.url)
        else:
            return await interaction.response.send_message("Please only attach an image file.", ephemeral=True)

    await vouch_channel.send(embed=embed)
    await interaction.response.send_message("✅ Your vouch has been posted!", ephemeral=True)

@bot.tree.command(name="say", description="Make the bot say something", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message="What the bot should say")
async def say(interaction: discord.Interaction, message: str):
    if not is_staff(interaction.user):
        return await interaction.response.send_message("No permission.", ephemeral=True)
    await interaction.channel.send(message)
    await interaction.response.send_message("✅ Sent.", ephemeral=True)

# ---------- RUN ----------
try:
    bot.run(BOT_TOKEN)
except Exception as e:
    print("\n========== ERROR ==========")
    print(e)
    print("===========================\n")
    input("Press Enter to close...")
