from discord.ext import commands, tasks
from discord import FFmpegPCMAudio, utils, PCMVolumeTransformer
import os, glob
import asyncio
import yt_dlp

class GroovyPersonal(commands.Cog):
  def __init__(self, bot, options=None):
    self.bot = bot
    self.extension = ".mp3"
    self.options = options or {
      "clean_cache": True
    }
    self.guild_params = {}
  
  def setup(self):
    for guild in self.bot.guilds:
      print(guild)

      this_dir = "./mp3s-cache/mp3s-"+str(guild.id)+"/"
      if not os.path.exists(this_dir):
        os.makedirs(this_dir)
      self.guild_params[guild.id] = {
        "players": None,
        "song_queue": [],
        "mp3_directory": this_dir,
        "running": False,
        "paused": False
      }
  
  @commands.Cog.listener()
  async def on_ready(self):
    print(f'{self.bot.user} is connected')
    self.setup()

  @commands.command(
    help="Starts looping and waits to play songs put in queue.",
    brief="Begin playing the queue."
  )
  async def begin(self, ctx):
    if(not ctx.author.voice):
      await ctx.send("You are not in a voice channel, you must be in a voice channel to run this command!")
      return
    if(self.guild_params[ctx.guild.id]["running"]):
      await ctx.send("Already running!")
      return

    await ctx.send("Success! Please add a song to play.")

    self.guild_params[ctx.guild.id]["running"] = True
    mp3_dir = self.guild_params[ctx.guild.id]['mp3_directory']
    while(self.guild_params[ctx.guild.id]["running"]):
      voice = await self.connect_if_necessary(ctx)

      songsAreQueued = len(self.guild_params[ctx.guild.id]["song_queue"]) > 0
      ispaused = self.guild_params[ctx.guild.id]["paused"]

      if(songsAreQueued and not voice.is_playing() and not ispaused):

        song_info = self.guild_params[ctx.guild.id]["song_queue"].pop(0)
        self.guild_params[ctx.guild.id]["song_queue"].append(song_info)
        [url, meta] = song_info

        await ctx.send("Prepping next song...")
        song_id = meta['id'] + self.extension
        if not glob.glob(mp3_dir + song_id):
          song_id = await self.download_song(url, mp3_dir)
          
        await ctx.send("Now playing " + meta['title'])
        await self.play_song(voice, mp3_dir + song_id)
        self.guild_params[ctx.guild.id]["players"] = voice
      else:
        await asyncio.sleep(1)

    # running is now false, reset
    self.guild_params[ctx.guild.id]["song_queue"].clear()

    try:
      self.guild_params[ctx.guild.id]["players"].stop()
    except:
      print("Couldn't stop the player.")

    self.guild_params[ctx.guild.id]["players"] = None

    try:
      await ctx.voice_client.disconnect()
    except:
      print("Couldn't disconnect.")
    
    await ctx.send("See you next time :)")

    # delete all temp files if we want to clean cache
    await asyncio.sleep(3)
    if(self.options["clean_cache"]):
      filelist = glob.glob(os.path.join(mp3_dir, "*"+self.extension))
      for f in filelist:
        os.remove(f)

  @commands.command(
    help="Flags the player to end the music bot and disconnects. Dequeing all songs in process.",
    brief="Ends the music playing session."
  )
  async def end(self, ctx):
    self.guild_params[ctx.guild.id]["running"] = False

  @commands.command(
    help="Skips the current song and goes to the next.",
    brief="Skips currently playing songs."
  )
  async def skip(self, ctx):
    voice_player = self.guild_params[ctx.guild.id]["players"]
    if(voice_player):
      voice_player.stop()

  @commands.command(
    help="Pauses current song.",
    brief="Pauses current song."
  )
  async def pause(self, ctx):
    voice_player = self.guild_params[ctx.guild.id]["players"]
    if(voice_player):
      voice_player.pause()
      self.guild_params[ctx.guild.id]["paused"] = True

  @commands.command(
    help="Resumes current song.",
    brief="Resumes current song."
  )
  async def resume(self, ctx):
    voice_player = self.guild_params[ctx.guild.id]["players"]
    if(voice_player):
      voice_player.resume()
      self.guild_params[ctx.guild.id]["paused"] = False

  @commands.command(
    help="Queue up a song and insert at the end of the queue",
    brief="Queue a song to be played."
  )
  async def add(self, ctx, url=None):
    if(url):
      song_info = [url, self.getMetaData(url)]
      self.guild_params[ctx.guild.id]["song_queue"].append(song_info)
      await ctx.send(song_info[1]['title'] + " has been added!")
    else:
      await ctx.send("Please provide a url.")

  @commands.command(
    help="Lets you see the name and index of the desired number of entries in the queue.",
    brief="View the queue."
  )
  async def view(self, ctx, n=10):
    queue = self.guild_params[ctx.guild.id]["song_queue"]
    if(len(queue) <= 0):
      await ctx.send("No songs in queue.")
      return

    response = "Next " + str(n) + " songs:\n"
    for i in range(n):
      if(len(queue) > i):
        song_info = queue[i]
        meta = song_info[1]
        response = response + "(" + str(i+1) + ") " + meta['title'] + "\n"
    await ctx.send("`" + response + "`")

  @commands.command(
    help="Allows you to input a number to remove from the queue. View what is in the queue with the view command.",
    brief="Remove a item from the queue"
  )
  async def remove(self, ctx, item_number=None):
    if(item_number == None):
      await ctx.send("Must provide a number in the queue to remove.")
      return
    [url, meta] = self.guild_params[ctx.guild.id]["song_queue"].pop(int(item_number)-1)
    await ctx.send("Removed " + meta['title'])

  @commands.command(
    help="Scale the volume by a given factor.",
    brief="Scale the volume up or down."
  )
  async def volume(self, ctx, vol=1):
    voice_player = self.guild_params[ctx.guild.id]["players"]
    if(voice_player):
      voice_player.source = PCMVolumeTransformer(voice_player.source, volume=vol)

  @commands.command(
    help="Clears the cache inside server.",
    brief="Clear cache."
  )
  async def clearcache(self, ctx):
    mp3_dir = self.guild_params[ctx.guild.id]['mp3_directory']
    filelist = glob.glob(os.path.join(mp3_dir, "*"+self.extension))
    for f in filelist:
      os.remove(f)

  async def play_song(self, voice, path, volume=0.25):
    try:
      source = FFmpegPCMAudio(path)
      voice.play(source)
      voice.source = PCMVolumeTransformer(voice.source, volume=volume)
    except:
      print("Could not play for some reason.")

  async def download_song(self, url, directory):
    ydl_opts = {
        'outtmpl': './'+directory+'/%(id)s.%(ext)s',
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
    return meta['id'] + self.extension

  def getMetaData(self, url):
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        "format": "bestaudio/best",
        "postprocessors": [{
          'key': 'FFmpegExtractAudio',
          "preferredcodec": "mp3",
          "preferredquality": "192"
        }]
      }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      meta = ydl.extract_info(url, download=False)
    return meta

  async def connect_if_necessary(self, ctx):
    try:
      channel = ctx.message.author.voice.channel
      if(not self.is_connected(ctx)):
        voice = await channel.connect()
      else:
        voice = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    
      return voice
    except:
      print("Error trying to connect to channel")

  def is_connected(self, ctx):
    voice_client = utils.get(ctx.bot.voice_clients, guild=ctx.guild)
    return voice_client and voice_client.is_connected()