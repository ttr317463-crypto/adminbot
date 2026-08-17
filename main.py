import discord
from discord.ext import commands
from discord.ui import Button, View
import os
from flask import Flask
from threading import Thread

# --- 無料Web Serviceのスリープ防止用Webサーバー設定 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    # Renderが指定するポート、またはデフォルトの8080番で起動
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()
# -----------------------------------------------------

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
MANAGEMENT_CHANNEL_ID = 1538731038702964818  # あなたの運営用チャンネルID
PUBLIC_CHANNEL_ID = 1538731424042061894      # あなたの一般公開チャンネルID

IMAGE_ONLINE_URL = "https://cdn.discordapp.com/attachments/1505128613090168853/1538730833748299786/6DFB3956-67F1-40E0-8F5D-E6F0CBF97AE0.png?ex=6a83be43&is=6a826cc3&hm=8d1053f0d977f90b83c2ebca4c49ff80b9c7850a2f6e91d22191b68617cd7009&"
IMAGE_SLEEP_URL = "https://cdn.discordapp.com/attachments/1505128613090168853/1538730292297207869/7B94AEC6-FB0F-4DD7-A870-D21C7329A46F.png?ex=6a83bdc1&is=6a826c41&hm=8ea8ac40ee7eefb6df0454b11b8ff881877905662ceb679b7fbc115e1e02a636&"

target_msg_id = None

class StatusControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message("❌ このボタンは管理者しか使用できません。", ephemeral=True)
        return False

    @discord.ui.button(label="Online", style=discord.ButtonStyle.green, custom_id="status_online")
    async def online_button(self, interaction: discord.Interaction, button: Button):
        await self.update_status(interaction, "🟢 tayu is Online", "Online", discord.Color.green(), IMAGE_ONLINE_URL)

    @discord.ui.button(label="Sleep", style=discord.ButtonStyle.secondary, custom_id="status_sleep")
    async def sleep_button(self, interaction: discord.Interaction, button: Button):
        await self.update_status(interaction, "💤 Sleep", "Sleep", discord.Color.dark_gray(), IMAGE_SLEEP_URL)

    async def update_status(self, interaction: discord.Interaction, title, description, color, image_url):
        global target_msg_id
        bot = interaction.client
        public_channel = bot.get_channel(PUBLIC_CHANNEL_ID)
        
        if public_channel is None:
            await interaction.response.send_message("一般向けチャンネルが見つかりません。", ephemeral=True)
            return

        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_image(url=image_url)
        
        if target_msg_id:
            try:
                msg = await public_channel.fetch_message(target_msg_id)
                await msg.edit(embed=embed)
                await interaction.response.send_message("ステータスを更新しました。", ephemeral=True)
                return
            except discord.NotFound:
                pass

        msg = await public_channel.send(embed=embed)
        target_msg_id = msg.id
        await interaction.response.send_message("初期メッセージを作成しました。", ephemeral=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(StatusControlView())

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    management_channel = bot.get_channel(MANAGEMENT_CHANNEL_ID)
    if management_channel:
        await management_channel.send("【運営専用】ステータス切り替えパネル：", view=StatusControlView())

if TOKEN:
    # Webサーバーを先に起動してからBotを動かす
    keep_alive()
    bot.run(TOKEN)
else:
    print("エラー: DISCORD_BOT_TOKEN が環境変数に設定されていません。")
