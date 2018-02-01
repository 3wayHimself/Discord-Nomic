# These are the dependecies. The bot depends on these to function, hence the name. Please do not change these unless your adding to them, because they can break the bot.
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import pickle

# Here you can modify the bot's prefix and description and wether it sends help in direct messages or not.
theBot = Bot(description="Squid Nomic bot for Discord", command_prefix="!", pm_help = False)
client = discord.Client()


# This section is for global variables
users = {}
generation_period = 5 # The number of seconds between each generation event
generation_amount = 5 # The number of watts to be added every second
update_msg = None # Reference to the message to keep updated

# This is what happens everytime the bot launches. In this case, it prints information like server count, user count the bot is connected to, and the bot id in the console.
# Do not mess with it because the bot can break.
@theBot.event
async def on_ready():
    print('Logged in as '+theBot.user.name+' (ID:'+theBot.user.id+') | Connected to '+str(len(theBot.servers))+' servers | Connected to '+str(len(set(theBot.get_all_members())))+' users')
    print('--------')
    print('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__, platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(theBot.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8'.format(theBot.user.id))
    return await theBot.change_presence(game=discord.Game(name='Nomic'))


# This section is for custom commands.
@theBot.command(pass_context=True)
async def ping(ctx):
	await theBot.say(":ping_pong: Pong!")


@theBot.command(pass_context=True)
async def hello(ctx):
    msg = 'Hello {0.author.mention}'.format(ctx.message)
    await theBot.say(msg)


@theBot.command(pass_context=True)
async def save(ctx):
    with open("./data/users.pickle", 'wb') as out_s: # open the file for writing
        for key, value in users.items():
            pickle.dump(value, out_s) # write the object to the file


@theBot.command(pass_context=True)
async def load(ctx):
    with open("./data/users.pickle", 'rb') as in_s: #open the file for reading
        while True:
            try:
                o = pickle.load(in_s) # read the next object from file
                users[o.name] = o # load the object into the list
            except EOFError: # We have finished the file
                break # so we can leave the loop


@theBot.command(pass_context=True)
async def join(ctx):
    if not str(ctx.message.author) in users: # if the user isn't already in the list
        users[str(ctx.message.author)] = User(str(ctx.message.author))


@theBot.command(pass_context=True)
async def adduser(ctx):
    inMess = ctx.message.content[9:] # Strip the command from the input. The command is 7 characters, plus the ! at the start, plus the space
    if not inMess: # If the string is now empty
        msg = 'No user specified'
        await theBot.say(inMess)
    else:
        if not str(inMess) in users: # if the user isn't already in the list
            users[inMess] = User(inMess)


@theBot.command(pass_context=True)
async def view(ctx):
    msg = ""
    for key, user in users.items():
        msg = msg + str(key) + ": " + str(user.watts) + " watts\n"
    global update_msg # indicate we want the global variable, not a local
    update_msg = await theBot.send_message(ctx.message.channel, msg) # send and save the update message


#this section is for custom classes
class User():
    def __init__(self, name):
        self.name = name
        self.watts = 0


# Put your other functions here
async def generatePower():
    while True: # set this up as an infinite loop
        for key, user in users.items():
            user.watts = user.watts + generation_amount # This adds the specified number of watts

        if update_msg is not None: # if we have set a place to update the display
            msg = ""
            for key, user in users.items():
                msg = msg + str(key) + ": " + str(user.watts) + " watts\n"
            await theBot.edit_message(update_msg, msg) # send the edit request
        await asyncio.sleep(generation_period) # wait a specified amount of time
asyncio.ensure_future(generatePower(), loop=client.loop) # Add this to the event scheduler


# These lines MUST be the end of the file. Any code after it might not run properly.
with open ("../.token", "r") as myfile:
    data=myfile.read()
theBot.run(data)
