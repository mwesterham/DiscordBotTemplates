from discord.ext import commands

class PingPong(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
  
  @commands.command(
    help="Used to test if the bot is active and replys pong.",
    brief="Replys pong."
  )
  async def ping(self, ctx):
    await ctx.send("pong!")