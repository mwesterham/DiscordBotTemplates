from discord.ext import commands, tasks
from datetime import datetime, timedelta
from pytz import timezone
import asyncio

class DailyStandup(commands.Cog):
  def __init__(self, bot, options):
    options['timezone'] = timezone(options['timezone'])
    
    self.bot = bot
    self.options = options
    self.standup_channel = None

  @commands.Cog.listener()
  async def on_ready(self):
    print(f'{self.bot.user} is connected')

  @tasks.loop(hours=24.0)
  async def loop(self):
    d = datetime.now(self.options["timezone"])
    if d.weekday() <= 4: # it is the weekday
      await self.standup_channel.send(self.options["daily_message"])

  @commands.command(
    help="Starts the daily stand up bot, posting daily",
    brief="Starts bot messages."
  )
  async def start(self, ctx):
    if(self.standup_channel != None):
      await ctx.send("Standup is already running, please stop current standup and retry starting.")
      return

    self.standup_channel = ctx.channel
    milliTill = self.getMilliTill(self.options["daily_start_hr"], self.options["daily_start_min"])
    await ctx.send("Time till next standup: " + self.getHumanReadable(milliTill))
    
    await asyncio.sleep(milliTill/1000)
    try:
      self.loop.start()
    except RuntimeError:
      print("RuntimeError occurred when starting the loop")
    except:
      print("Some other error occurred when starting the loop")

  @commands.command(
    help="Stops the daily stand up bot from posting daily",
    brief="Stops bot messages."
  )
  async def stop(self, ctx):
    try:
      self.standup_channel = None
      self.loop.cancel()
      await ctx.send("Stopped standup")
    except RuntimeError:
      print("RuntimeError occurred when cancelling the loop")
    except:
      print("Some other error occurred when cancelling the loop")

  @commands.command(
    help="Notifies chat if standup is running how much time is left till the next standup.",
    brief="Gives info on the current standup."
  )
  async def info(self, ctx):
    if(self.standup_channel == None):
      await ctx.send("No standup is currently running.")
    else:
      milliTill = self.getMilliTill(self.options["daily_start_hr"], self.options["daily_start_min"])
      await ctx.send("Standup is currently running.\nTime till next standup: " + self.getHumanReadable(milliTill))

  @commands.command(
    help="Forces the start of a daily stand up and sends a message.",
    brief="Force start daily stand up."
  )
  async def force(self, ctx):
    await ctx.send(self.options["daily_message"])

  def getMilliTill(self, hour, minutes):
    now = datetime.now(self.options["timezone"])
    target_time = self.options["timezone"].localize(datetime(now.year, now.month, now.day, hour, minutes))
    if now > target_time:
      target_time = target_time + timedelta(days = 1)
    return (target_time - now).total_seconds() * 1000

  def getHumanReadable(self, ms):
    seconds=int((ms/1000)%60)
    minutes=int((ms/(1000*60))%60)
    hours=int((ms/(1000*60*60))%24)
    return str(hours) + " hours, " + str(minutes) + " minutes, " + str(seconds) + " seconds"