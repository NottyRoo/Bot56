import discord
from discord.ext import commands
import aiohttp
import io
from urllib.parse import urlparse
import sys

sys.stdout.reconfigure(encoding='utf-8')

TOKEN = "MTI1MzkzMzMwMjAzMzY3ODQ3Nw.Gfbw4I.ZtoxL3WG_UIkKlmp3ZdIAoJwVZkolkDcpMcbfI"
API_TOKEN = "DGMW"
ALLOWED_CHANNEL_ID = 1404524957764943902
ADMIN_ID = 1021300788431163392

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ---------- Modal สำหรับกรอก URL ----------
class UrlModal(discord.ui.Modal, title="🔍 ค้นหา URL"):
    url_input = discord.ui.TextInput(
        label="กรุณาใส่ URL ที่ต้องการค้นหา",
        style=discord.TextStyle.short,
        placeholder="https://example.com",
        required=True
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        query = self.url_input.value.strip()

        blocked_domains = [
            "mybusiness.dtac.co.th",
            "crmlite-dealer.truecorp.co.th",
            "aisapponline.ais.co.th",
            "flashexpress.co.th",
            "bo.psg777.com",
            "psis.me",
            "sso.dxc.go.th"
        ]

        for domain in blocked_domains:
            if domain in query:
                await interaction.response.send_message("🚫 ไม่สามารถค้นหาเว็บไซต์นี้ไอ่หน้าโง่", ephemeral=True)
                return

        parsed_url = urlparse(query if query.startswith("http") else "http://" + query)
        hostname = parsed_url.netloc or parsed_url.path

        url = f"https://api404xcode.elementfx.com/vip?q={query}&k={API_TOKEN}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://api404xcode.elementfx.com/"
        }

        async with aiohttp.ClientSession() as session:
            try:
                # แจ้งกำลังค้นหา (ephemeral)
                await interaction.response.send_message(f"🔍 กำลังค้นหา : `{query}`", ephemeral=True)

                async with session.get(url, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    result = await response.text()

                total_found = len(result.splitlines())
                file = discord.File(fp=io.StringIO(result), filename=f"{hostname}.txt")

                # ส่งไฟล์แบบ ephemeral → เฉพาะผู้สั่งเห็น
                await interaction.followup.send("📄 ผลลัพธ์ของคุณ", file=file, ephemeral=True)

                # แจ้ง ADMIN
                try:
                    admin_user = await bot.fetch_user(ADMIN_ID)
                    embed = discord.Embed(
                        title="🔍 การค้นหา URL",
                        color=discord.Color.blue(),
                        timestamp=interaction.message.created_at
                    )
                    embed.add_field(name="👤 ผู้ใช้", value=f"{self.user} ({self.user.id})", inline=False)
                    embed.add_field(name="🔗 URL", value=query, inline=False)
                    embed.add_field(name="📄 จำนวน", value=f"{total_found} บรรทัด", inline=False)
                    embed.set_footer(text="การแจ้งเตือนจากบอท")

                    await admin_user.send(embed=embed)
                except discord.errors.Forbidden:
                    pass

            except Exception as e:
                await interaction.followup.send("❌ เกิดข้อผิดพลาดในการค้นหา", ephemeral=True)


# ---------- ปุ่มกด ----------
class UrlSearchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔍 ค้นหา URL", style=discord.ButtonStyle.primary)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.id != ALLOWED_CHANNEL_ID:
            await interaction.response.send_message("🚫 ไม่สามารถใช้ปุ่มนี้ในช่องนี้ได้", ephemeral=True)
            return
        modal = UrlModal(user=interaction.user)
        await interaction.response.send_modal(modal)


@bot.event
async def on_ready():
    print(f"✅ บอททำงานแล้วในชื่อ {bot.user}")
    channel = bot.get_channel(ALLOWED_CHANNEL_ID)
    if channel:
        view = UrlSearchView()

        # สร้าง Embed พร้อม GIF
        embed = discord.Embed(
            title="🔍 ค้นหา URL",
            description="กดปุ่มด้านล่างเพื่อค้นหา URL\nผลลัพธ์จะปรากฏเฉพาะคุณ",
            color=discord.Color.blue()
        )
        embed.set_image(url="https://media.giphy.com/media/3o7aD2saalBwwftBIY/giphy.gif")  # ตัวอย่าง GIF

        # ข้อความใต้ GIF
        embed.set_footer(text="📌 โปรดกรอก URL ที่ต้องการค้นหาอย่างระมัดระวัง")

        await channel.send(embed=embed, view=view)


bot.run(TOKEN)
