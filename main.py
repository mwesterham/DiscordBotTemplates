# imports
import os
from discord.ext import commands
from cogs.GroovyPersonal import GroovyPersonal

# Grab credentials and info from environment variables
TOKEN = os.getenv('DISCORD_TOKEN')

# Set options
options = {}

# Client instantiation
client = commands.Bot(command_prefix=".")
client.add_cog(GroovyPersonal(client, options))
client.run(TOKEN)