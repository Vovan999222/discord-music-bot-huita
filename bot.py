import discord
from discord.ext import commands
from discord import app_commands
from config import BOT_TOKEN
import yt_dlp
import asyncio

# НАСТРОЙКИ РОЛЕЙ
class Roles:
    OWNER = ""

    # Роли для команд музыки (/play, /skip и т.д.)
    MUSIC = ["", OWNER] 

def is_owner_role():
    async def predicate(ctx):
        if not Roles.OWNER or not Roles.OWNER.strip():
            raise commands.CheckFailure("ConfigError: В коде не указана роль владельца (`Roles.OWNER`)!")
        if hasattr(ctx.author, "roles") and any(role.name == Roles.OWNER for role in ctx.author.roles):
            return True
        raise commands.MissingRole(Roles.OWNER)
    return commands.check(predicate)

def has_music_roles():
    async def predicate(ctx):
        valid_roles = [r for r in Roles.MUSIC if r and r.strip()]
        if not valid_roles:
            raise commands.CheckFailure("ConfigError: В коде не указаны роли для доступа к музыке (`Roles.MUSIC`)!")
        if hasattr(ctx.author, "roles") and any(role.name in valid_roles for role in ctx.author.roles):
            return True
        raise commands.MissingAnyRole(valid_roles)
    return commands.check(predicate)

YDL_OPTS = {
    'format': 'bestaudio[protocol^=http]/bestaudio[ext=mp3]/bestaudio[acodec!=opus]/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
queues = {}

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    print('Если команды не видны в меню Discord, напишите: !sync')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure) and "ConfigError:" in str(error):
        msg = str(error).split("ConfigError: ")[1]
        await ctx.send(f"⚠️ **Ошибка настройки бота:** {msg}\n*Администратор должен вписать названия ролей в класс `Roles` в коде.*")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(f"❌ У вас нет нужной роли! Требуется: **{error.missing_role}**")
    elif isinstance(error, commands.MissingAnyRole):
        roles_list = ", ".join(error.missing_roles)
        await ctx.send(f"❌ Нет прав! Для этой команды нужна хотя бы одна из ролей: **{roles_list}**")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"⚠️ Произошла ошибка: {error}")

async def play_next(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        link = queues[ctx.guild.id].pop(0)
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            try:
                info = await asyncio.to_thread(ydl.extract_info, link['url'], download=False)
                url = info['url']
                title = info.get('title', 'Трек')
            except Exception as e:
                print(f"Ошибка получения ссылки: {e}")
                await play_next(ctx)
                return

        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

        if voice_client and voice_client.is_connected():
            try:
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(url, executable='ffmpeg', **FFMPEG_OPTIONS)
                )
                source.volume = 1.0

                def after_playing(error):
                    if error:
                        print(f"Ошибка аудио: {error}")
                    asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
                voice_client.play(source, after=after_playing)
                await ctx.send(f'▶️ **Сейчас играет:** {title}')
            except Exception as e:
                print(f"❌ Ошибка воспроизведения: {e}")
                await play_next(ctx)

@bot.hybrid_command(name='help', description="Список всех команды")
@has_music_roles()
async def help(ctx):
    embed = discord.Embed(
        title="🎧 Музыкальный Бот",
        description="Список доступных команд для управления:",
        color=discord.Color.blue()
    )
    embed.add_field(name="▶️ /play [название/ссылка]", value="Включить трек или добавить в очередь", inline=False)
    embed.add_field(name="⏭️ /skip", value="Пропустить текущий трек", inline=True)
    embed.add_field(name="⏸️ /pause", value="Пауза", inline=True)
    embed.add_field(name="▶️ /resume", value="Продолжить", inline=True)
    embed.add_field(name="📜 /queue", value="Показать текущую очередь", inline=True)
    embed.add_field(name="🛑 /stop", value="Остановить и выйти", inline=True)
    embed.add_field(name="🔊 /volume [0-100]", value="Изменить громкость", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='sync')
@is_owner_role()
async def sync(ctx):
    msg = await ctx.send("🔄 Синхронизация команд...")
    try:
        s = await bot.tree.sync()
        await msg.edit(content=f"✅ Команды синхронизированы: {len(s)} шт. (Нажмите Ctrl+R)")
    except Exception as e:
        await msg.edit(content=f"❌ Ошибка: {e}")

@bot.hybrid_command(name='play', description="Включить трек или добавить его в очередь")
@has_music_roles()
@app_commands.describe(query="Напишите название песни или вставьте ссылку на YouTube")
async def play(ctx, *, query: str):
    await ctx.defer()
    if not ctx.author.voice:
        await ctx.send("❌ Зайди в голосовой канал!")
        return
    vc = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)

    if voice_client is None:
        await vc.connect()
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    elif voice_client.channel != vc:
        await voice_client.move_to(vc)

    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []

    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        try:
            target = query if query.startswith('http') else f"ytsearch:{query}"
            info = await asyncio.to_thread(ydl.extract_info, target, download=False)

            added = False
            first_title = ""

            entries = info.get('entries')
            if entries:
                if query.startswith('http'): 
                    for entry in entries:
                        if entry:
                            queues[ctx.guild.id].append({'url': entry['url'], 'title': entry.get('title', 'Трек')})
                            added = True
                    first_title = f"Плейлист ({len(entries)} шт.)"
                elif len(entries) > 0:
                    top = entries[0]
                    queues[ctx.guild.id].append({'url': top['url'], 'title': top.get('title', 'Трек')})
                    first_title = top.get('title', 'Трек')
                    added = True
            else:
                queues[ctx.guild.id].append({'url': info['webpage_url'], 'title': info.get('title', 'Трек')})
                first_title = info.get('title', 'Трек')
                added = True

            if not added:
                await ctx.send("❌ Ничего не найдено.")
                return
            if voice_client.is_playing() or voice_client.is_paused():
                queue_pos = len(queues[ctx.guild.id])
                await ctx.send(f"✅ В очередь добавлено: **{first_title}** (позиция: {queue_pos})")
            else:
                if ctx.interaction:
                    try:
                        await ctx.interaction.delete_original_response()
                    except discord.NotFound:
                        pass

            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next(ctx)

        except Exception as e:
            print(f"Ошибка play: {e}")
            await ctx.send("⚠️ Ошибка. Попробуйте другую ссылку.")

@bot.hybrid_command(name='skip', description="Пропустить текущий трек")
@has_music_roles()
async def skip(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏭️ Пропуск!")
    else:
        await ctx.send("Нечего пропускать.")

@bot.hybrid_command(name='pause', description="Поставить воспроизведение на паузу")
@has_music_roles()
async def pause(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ **Пауза** (напиши `/resume` чтобы продолжить)")

@bot.hybrid_command(name='resume', description="Продолжить воспроизведение")
@has_music_roles()
async def resume(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Продолжаем.")

@bot.hybrid_command(name='volume', description="Изменить громкость воспроизведения (0-100)")
@has_music_roles()
@app_commands.describe(vol="Укажите уровень громкости от 0 до 100")
async def volume(ctx, vol: int):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.source:
        if 0 <= vol <= 100:
            vc.source.volume = vol / 100
            await ctx.send(f"🔊 Громкость: {vol}%")
        else:
            await ctx.send("Число должно быть от 0 до 100.")
    else:
        await ctx.send("Музыка не играет.")

@bot.hybrid_command(name='stop', description="Остановить музыку и отключить бота")
@has_music_roles()
async def stop(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if ctx.guild.id in queues: queues[ctx.guild.id].clear()
    if vc:
        if vc.is_playing(): vc.stop()
        await vc.disconnect()
        await ctx.send("Воспроизведение остановлено, бот отключен от канала.")

@bot.hybrid_command(name='queue', description="Показать текущую очередь треков")
@has_music_roles()
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        list_s = "\n".join([f"{i+1}. {s['title']}" for i, s in enumerate(queues[ctx.guild.id][:10])])
        msg = f"📜 **Очередь:**\n{list_s}"
        if len(queues[ctx.guild.id]) > 10: msg += "\n*...и другие*"
        await ctx.send(msg)
    else:
        await ctx.send("📭 Очередь пуста.")

bot.run(BOT_TOKEN)
