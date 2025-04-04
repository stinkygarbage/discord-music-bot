import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
import logging
from datetime import timedelta

# Load config
from config import TOKEN

# Logging setup
log_dir = "/var/log/music-bot"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, "bot.log"),
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(name)s: %(message)s",
)

# Intents and bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Globals
queue = asyncio.Queue()
now_playing = None
loop_mode = "off"  # off, one, all
volume_level = 0.5

# yt-dlp and ffmpeg options
ydl_opts = {'format': 'bestaudio'}
ffmpeg_opts = {'options': '-vn'}

# Ensure download directory exists
if not os.path.exists('downloads'):
    os.makedirs('downloads')

# Helpers
async def ensure_voice(interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ You're not in a voice channel.")
        return None
    vc = interaction.guild.voice_client
    if vc:
        return vc
    return await interaction.user.voice.channel.connect()

async def stream_audio(vc, url):
    ffmpeg_options = {'options': '-vn'}
    vc.play(discord.FFmpegPCMAudio(url, **ffmpeg_options))
    while vc.is_playing():
        await asyncio.sleep(1)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    print(f'✅ Bot is ready as {bot.user}')

@bot.tree.command(name="play", description="Play a song or playlist from YouTube")
async def play(interaction: discord.Interaction, url: str):
    await interaction.response.defer()
    await queue.put(url)
    await interaction.followup.send(f"🎶 Added to queue: {url}")
    if not interaction.guild.voice_client:
        await ensure_voice(interaction)
        bot.loop.create_task(player_loop(interaction.guild))

async def player_loop(guild):
    global now_playing
    vc = guild.voice_client
    while True:
        url = await queue.get()
        now_playing = url
        await announce_now_playing(guild, url)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                entries = info['entries']
                for entry in entries:
                    await stream_audio(vc, entry['url'])
            else:
                await stream_audio(vc, info['url'])
        if loop_mode == "one":
            await queue.put(url)
        elif queue.empty():
            await vc.disconnect()
            break

async def announce_now_playing(guild, url):
    text_channel = discord.utils.get(guild.text_channels, name="music-bot")
    if not text_channel:
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        text_channel = await guild.create_text_channel("music-bot", overwrites=overwrites)
    await text_channel.send(f"▶️ Now playing: {url}")

bot.run(TOKEN)
