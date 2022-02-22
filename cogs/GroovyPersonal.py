from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, utils, PCMVolumeTransformer
import os
import asyncio
import yt_dlp

class GroovyPersonal(commands.Cog):
  def __init__(self, bot, options):
    self.bot = bot
    self.options = options

    self.song_queue_urls = {}
    self.players = {}
  
  def setup(self):
    for guild in self.bot.guilds:
      print(guild.id)
      self.song_queue_urls[guild.id] = []
      self.players[guild.id] = None
  
  @commands.Cog.listener()
  async def on_ready(self):
    print(f'{self.bot.user} is connected')
    self.setup()

  @commands.command(
    help="Starts playing everything in the queue.",
    brief="Start playing a song."
  )
  async def play(self, ctx, url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"):
    if(ctx.author.voice):
      voice = await self.connect_if_necessary(ctx)

      self.song_queue_urls[ctx.guild.id].append(url)
      while(len(self.song_queue_urls[ctx.guild.id]) > 0):        
        url = self.song_queue_urls[ctx.guild.id].pop()

        song_id = await self.download_song(url)

        await self.play_song(voice, song_id)
        self.players[ctx.guild.id] = voice
        while(ctx.voice_client.is_playing()):
          await asyncio.sleep(1)
    else:
      await ctx.send("You are not in a voice channel, you must be in a voice channel to run this command!")
    await ctx.send("Finished playing queue!")

  @commands.command(
    help="Stops the current song from playing.",
    brief="Stops the current song."
  )
  async def stop(self, ctx):
    self.song_queue_urls[ctx.guild.id].clear()
    self.players[ctx.guild.id].stop()

  @commands.command(
    help="Skips the current song and goes to the next.",
    brief="Skips currently playing songs."
  )
  async def skip(self, ctx):
    self.players[ctx.guild.id].stop()

  @commands.command(
    help="Pauses current song.",
    brief="Pauses current song."
  )
  async def pause(self, ctx):
    self.players[ctx.guild.id].pause()

  @commands.command(
    help="Resumes current song.",
    brief="Resumes current song."
  )
  async def resume(self, ctx):
    self.players[ctx.guild.id].resume()

  @commands.command(
    help="Queue up a song and insert at the end of the queue",
    brief="Queue a song."
  )
  async def queue(self, ctx, url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"):
    self.song_queue_urls[ctx.guild.id].append(url)
  
  @commands.command(
    help="Used to test if the bot is active and replys pong.",
    brief="Replys pong."
  )
  async def ping(self, ctx):
    await ctx.send("pong!")

  async def play_song(self, voice, path, volume=0.25):
    source = FFmpegPCMAudio(path)
    voice.play(source)
    voice.source = PCMVolumeTransformer(voice.source, volume=volume)

  async def download_song(self, url, extension=".mp3"):
    ydl_opts = {
        'outtmpl': '%(id)s.%(ext)s',
        "format": "bestaudio/best",
        "postprocessors": [{
          'key': 'FFmpegExtractAudio',
          "preferredcodec": "mp3",
          "preferredquality": "192"
        }]
      }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      meta = ydl.extract_info(url, download=False)
      ydl.download([url])
    return meta['id'] + extension

  async def connect_if_necessary(self, ctx):
    channel = ctx.message.author.voice.channel
    if(not self.is_connected(ctx)):
      voice = await channel.connect()
    else:
      print("Already connected")
    return voice

  def is_connected(self, ctx):
    voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()