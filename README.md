# Discord Music Bot huita

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Enabled-red?style=for-the-badge&logo=youtube)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Enabled-green?style=for-the-badge&logo=ffmpeg)

This Discord bot is designed to seamlessly stream high-quality music directly into your voice channels. 

The bot automatically searches for tracks on YouTube, extracts the best available audio stream, and plays it with full support for queues, volume control, and modern Slash Commands.

## Features

**Music Playback**:
* Supports links and direct text search queries from **YouTube** and other platforms supported by `yt-dlp`.
* **Smart Queue System**: Add multiple tracks to the queue. The bot will automatically play the next track when the current one finishes.
* **Volume Control**: Easily adjust the playback volume (from 0 to 100%) on the fly.

**Modern Discord Integration**:
* **Slash Commands**: Fully utilizes Discord's modern `/` commands with built-in descriptions and argument hints for a great user experience.
* **Hybrid Commands**: Backward compatible with classic text commands (using the `!` prefix).

**Playback Control**:
* Full set of audio controls: `/play`, `/pause`, `/resume`, `/skip`, `/stop`, and `/queue`.

**Asynchronous & Non-blocking**:
* Track searching and metadata extraction run in background threads (`asyncio.to_thread`), ensuring the bot never freezes or disconnects from Discord while processing heavy requests.

## Requirements

To run the bot, you need:

1.  **Python 3.8+**
2.  **FFmpeg** (system-level) — critical for streaming raw audio to Discord voice channels.

### Installing FFmpeg:

**Ubuntu/Debian**:
```bash
sudo apt update && sudo apt upgrade && sudo apt install ffmpeg
```

**Windows**:
* **Method 1 (Recommended):** Open a terminal (PowerShell or CMD) and run:
```cmd
winget install Gyan.FFmpeg
```
> **⚠️ "winget" command not found?** If you are using an older version of Windows 10, download and install the **App Installer** from the [official GitHub releases](https://github.com/microsoft/winget-cli/releases) (look for the `.msixbundle` file).

* **Method 2 (Manual):** Download the archive from the [official repository](https://github.com/GyanD/codexffmpeg/releases), unzip it, and add the path to the `bin` folder to your system environment variables (PATH).
```cmd
C:\ffmpeg\bin
```

**MacOS**:
```bash
brew install ffmpeg
```

## Installation & Usage

### 1. Clone the repository

```bash
git clone [https://github.com/YourUsername/your-repo-name.git](https://github.com/YourUsername/your-repo-name.git)
cd your-repo-name
```

### 2. Create a virtual environment (Recommended)

```bash
python -m venv venv
```
Windows:
```
venv\Scripts\activate
```
Linux/Mac:
```
source venv/bin/activate
```

### 3. Install dependencies

You need to install `discord.py` (with voice support) and `yt-dlp`:

```bash
pip install "discord.py[voice]" yt-dlp
```

### 4. Configuration

**1. Set up the Bot Token:**
Create a `config.py` file in the root directory and insert your bot token from the [Discord Developer Portal](https://discord.com/developers/applications):
```python
BOT_TOKEN = ""
```

**2. Configure Role Access (Important!):**
Open `ds-bot.py` and find the `Roles` class at the top of the file. You **must** define the roles that are allowed to use the bot commands. 

```python
class Roles:
    # Role required to use the !sync command
    OWNER = "Owner Role Name"
    
    # Roles allowed to use music commands (/play, /skip, etc.)
    MUSIC = ["Member", "DJ", OWNER] 
```
*Note: The bot features a self-diagnostic system. If you leave these role strings empty in the code, the bot will still start, but it will send a helpful `ConfigError` message in the chat reminding the admin to set up the roles.*

### 5. Run the bot

```bash
python ds-bot.py
```

### 6. Syncing Slash Commands

When you invite the bot to your server for the first time, its Slash Commands might not appear immediately. 
To fix this, type the following command in any text channel on your server:
```text
!sync
```
*After seeing the success message, press `Ctrl + R` (or `Cmd + R` on Mac) to refresh your Discord client cache.*

## Technical Details

* **Voice Engine**: Uses `discord.FFmpegPCMAudio` combined with `discord.PCMVolumeTransformer` for dynamic audio manipulation.
* **Reconnect Flags**: FFmpeg is configured with `-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5` to ensure stable playback even if the network connection to the media server drops briefly.
* **Heartbeat Protection**: `yt-dlp` extraction is offloaded to native `asyncio` threads. This prevents the event loop from blocking, eliminating `Voice heartbeat blocked` timeouts and random bot disconnects.

## License

This project is distributed under the [MIT License](https://raw.githubusercontent.com/Vovan999222/discord-music-bot-huita/refs/heads/main/LICENSE)
