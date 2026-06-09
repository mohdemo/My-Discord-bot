import os
os.system("pip install discord.py")

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

RULEBOOK_URL = "https://example.com/rulebook"

active_tickets_channel_to_user = {}
active_tickets_user_to_channel = {}

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
    except Exception:
        pass

class MainMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Rulebook | دليل البطولة", url=RULEBOOK_URL, row=0))

    @discord.ui.button(label="Open Support Ticket | فتح تذكرة دعم", style=discord.ButtonStyle.primary, custom_id="open_ticket_btn", row=1)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=180)
        select = discord.ui.Select(
            placeholder="Choose PMNC | اختر البطولة...",
            options=[
                discord.SelectOption(label="Algeria 🇩🇿", value="Algeria"),
                discord.SelectOption(label="Egypt 🇪🇬", value="Egypt"),
                discord.SelectOption(label="Iraq 🇮🇶", value="Iraq"),
                discord.SelectOption(label="Jordan 🇯🇴", value="Jordan"),
                discord.SelectOption(label="KSA 🇸🇦", value="KSA"),
                discord.SelectOption(label="Lebanon 🇱🇧", value="Lebanon"),
                discord.SelectOption(label="Libya 🇱🇾", value="Libya"),
                discord.SelectOption(label="Morocco 🇲🇦", value="Morocco"),
                discord.SelectOption(label="Sudan 🇸🇩", value="Sudan"),
                discord.SelectOption(label="Syria 🇸🇾", value="Syria"),
                discord.SelectOption(label="Tunisia 🇹🇳", value="Tunisia"),
                discord.SelectOption(label="UAE 🇦🇪", value="UAE"),
                discord.SelectOption(label="Wildcard 🌍", value="Wildcard"),
            ]
        )
        
        async def select_callback(inter: discord.Interaction):
            pmnc = select.values[0]
            guild = inter.guild
            user = inter.user
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
            }
            
            channel = await guild.create_text_channel(
                name=f"ticket-{pmnc.lower()}-{user.name}",
                overwrites=overwrites,
                topic=f"Ticket opened by {user.name} ({user.id}) for PMNC: {pmnc}"
            )
            
            active_tickets_channel_to_user[channel.id] = user.id
            active_tickets_user_to_channel[user.id] = channel.id
            
            embed = discord.Embed(
                title=f"🎫 {pmnc} — Support Ticket",
                description=f"Opened by **{user.name}** ({user.id}) via DM.\n**PMNC:** {pmnc}\n\n💬 Messages sent by the user in DM will appear here.\nReply in this channel and your message will be forwarded to their DM.",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
            
            try:
                close_view = discord.ui.View(timeout=None)
                close_btn = discord.ui.Button(label="🔒 Close Ticket | إغلاق التذكرة", style=discord.ButtonStyle.danger, custom_id=f"close_{channel.id}")
                
                async def close_callback(c_inter: discord.Interaction):
                    ch_id = int(close_btn.custom_id.split('_')[1])
                    target_channel = bot.get_channel(ch_id)
                    if target_channel:
                        await target_channel.delete()
                    
                    u_id = active_tickets_channel_to_user.pop(ch_id, None)
                    if u_id:
                        active_tickets_user_to_channel.pop(u_id, None)
                        
                    await c_inter.response.send_message("Ticket closed successfully. / تم إغلاق التذكرة بنجاح.")
                
                close_btn.callback = close_callback
                close_view.add_item(close_btn)
                
                await user.send(
                    f"✅ Ticket opened for **{pmnc}**!\n✅ تم فتح تذكرتك لـ **{pmnc}**!\n\nYou can now type your message here and staff will reply in this DM.\nيمكنك الآن كتابة رسالتك هنا وسيرد عليك الطاقم في هذه المحادثة مباشرة.",
                    view=close_view
                )
                await inter.response.send_message("🎟️ Ticket created! Check your DMs. / تم إنشاء التذكرة، تفقد الخاص بك.", ephemeral=True)
            except discord.Forbidden:
                await inter.response.send_message("❌ Cannot open ticket. Please enable your Direct Messages (DMs).", ephemeral=True)
                await channel.delete()

        select.callback = select_callback
        view.add_item(select)
        await interaction.response.send_message("Please select your tournament below:", view=view, ephemeral=True)

    @discord.ui.button(label="I'm fine | تمام", style=discord.ButtonStyle.secondary, custom_id="im_fine_btn", row=2)
    async def im_fine(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Done ✅ If you need anything later, send any message.\nتم ✅ إذا احتجت أي شيء لاحقًا، أرسل أي رسالة.",
            ephemeral=True
        )

@bot.tree.command(name="setup_panel", description="Post the main tournament support panel.")
@app_commands.guild_only()
@app_commands.checks.has_permissions(administrator=True)
async def setup_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏆 Tournament Support Center | مركز دعم البطولة",
        description="Welcome! Use the options below to read the rules or open a private ticket with the organization staff.\n\nأهلاً بك! استخدم الخيارات أدناه لقراءة القوانين أو فتح تذكرة دعم خاصة مع طاقم المنظمين.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message("Panel posted.", ephemeral=True)
    await interaction.channel.send(embed=embed, view=MainMenuView())

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild is not None:
        user_id = active_tickets_channel_to_user.get(message.channel.id)
        if user_id:
            user = await bot.fetch_user(user_id)
            if user:
                try:
                    await user.send(f"**[STAFF] @{message.author.name}:** {message.content}")
                except discord.Forbidden:
                    await message.channel.send("❌ Cannot send DM to this user. Their DMs might be locked.")
            return

    if message.guild is None:
        channel_id = active_tickets_user_to_channel.get(message.author.id)
        if channel_id:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send(f"**{message.author.name}:** {message.content}")
            return

    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    if payload.guild_id is not None:
        user_id = active_tickets_channel_to_user.get(payload.channel_id)
        if user_id:
            user = await bot.fetch_user(user_id)
            if user:
                try:
                    await user.send(f"ℹ️ **[STAFF]** reacted with {payload.emoji} to your message.")
                except discord.Forbidden:
                    pass
            return

@bot.tree.command(name="bulkrole", description="Assign a role to up to 100+ users dynamically.")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_roles=True)
async def bulkrole(interaction: discord.Interaction, role: discord.Role, users_input: str):
    await interaction.response.defer(ephemeral=False)
    
    user_ids_or_mentions = re.split(r"[\s,\n]+", users_input.strip())
    
    parsed_count = 0
    updated_count = 0
    already_correct = 0
    not_found = 0
    failed = 0
    
    guild = interaction.guild
    
    for item in user_ids_or_mentions:
        if not item:
            continue
            
        clean_id = re.sub(r"[<@!>]", "", item)
        if not clean_id.isdigit():
            continue
            
        parsed_count += 1
        user_id = int(clean_id)
        
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                not_found += 1
                continue
            except Exception:
                failed += 1
                continue
                
        if role in member.roles:
            already_correct += 1
        else:
            try:
                await member.add_roles(role)
                updated_count += 1
            except Exception:
                failed += 1
                
        await asyncio.sleep(0.1)

    await interaction.followup.send(
        f"✅ Bulk role job finished in **{guild.name}** (`{role.id}`)\n"
        f"• IDs parsed: **{parsed_count}**\n"
        f"• Updated: **{updated_count}**\n"
        f"• Already correct: **{already_correct}**\n"
        f"• Not found in server: **{not_found}**\n"
        f"• Failed: **{failed}**"
    )

@bot.tree.command(name="clear", description="Purge messages in this channel.")
@app_commands.guild_only()
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    if amount <= 0:
        await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
        return
        
    await interaction.response.defer(ephemeral=True)
    try:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(
            f"✅ Cleared **{len(deleted)}** messages in this channel!\n"
            f"✅ تم مسح **{len(deleted)}** رسالة في هذه القناة!"
        )
    except discord.HTTPException:
        await interaction.followup.send(
            "⚠️ Some messages could not be deleted because they are older than 14 days.\n"
            "⚠️ لم يتم مسح بعض الرسائل لأنها أقدم من 14 يوماً (حدود ديسكورد)."
        )
    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {e}")

bot.run("MTUxMzkzNDMxMzA2ODk1Nzg1OA.GfDD1r.68GJU_WCuXVLAiz1KyeLz4sgcAKKPxcTFiGZ-M")
