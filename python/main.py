# These are the dependecies.
# The bot depends on these to function, hence the name.
# Please do not change these unless you're adding to them, because they can break the bot.
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import pickle


# This section is for global variables
theBot = Bot(description="Squid Nomic bot for Discord",
             command_prefix="!", pm_help=False)
users = {}
generation_period = 1
save_period = 60
update_period = 5
update_msg = None  # Reference to the message to keep updated
watt_win = 5000000


# this section is for custom classes
class User():
    def __init__(self, name, mention):
        self.name = name
        self.mention = mention
        self.data = {}

    def addPower(self):
        # how much space is left in the battery
        battery_room = self.getAttr("battery") - self.getAttr("watts")
        if battery_room > 0:
            if battery_room > self.getAttr("generation"):
                self.setAttr("watts", round(self.getAttr(
                    "watts") + self.getAttr("generation"), 2))
            else:
                global update_msg
                if update_msg is not None:
                    msg = self.mention + " has a full battery"
                    theBot.loop.create_task(sendMessage(update_msg.channel, msg))
                self.setAttr("watts", self.getAttr("battery"))
                self.setAttr("overflow", round(self.getAttr(
                    "overflow") + self.getAttr("generation") - battery_room, 2))
        else:
            self.setAttr("overflow", round(self.getAttr(
                "overflow") + self.getAttr("generation"), 2))
        if self.getAttr("overflow") >= watt_win:
            global update_msg
            if update_msg is not None:
                msg = "@" + self.mention + " has won"
                theBot.loop.create_task(sendMessage(update_msg.channel, msg))

    def getAttr(self, key):  # Get infor for this instance
        if key in self.data:
            return self.data[key]  # get a amount unique
        elif key == 'watts':  # otherwise, the following are default values
            return 0
        elif key == 'battery':
            return 100
        elif key == 'overflow':
            return 0
        elif key == 'generation':
            return generation_period
        else:
            return None  # if we reach this, the requested key was not found

    def setAttr(self, key, value):  # set the value of an attribute of this instance
        self.data[key] = value

    def consumePower(self, consumed):  # Attempt to consume power. Returns True if successful
        if self.getAttr("battery") > consumed:
            self.setAttr("battery", self.getAttr("battery") - consumed)
            return True
        else:
            return False


# This is what happens everytime the bot launches.
# Do not mess with it because the bot can break.
@theBot.event
async def on_ready():
    print('Logged in as '+theBot.user.name+' (ID:'+theBot.user.id+') | Connected to '
          + str(len(theBot.servers))+' servers | Connected to '
          + str(len(set(theBot.get_all_members())))+' users')
    print('--------')
    print('Current Discord.py Version: {} | Current Python Version: {}'.format(
        discord.__version__, platform.python_version()))
    print('--------')
    print('Use this link to invite {}:'.format(theBot.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=8'.format(
                                                                                    theBot.user.id))
    with open("./data/users.pickle", 'rb') as in_s:  # open the file for reading
        while True:
            try:
                o = pickle.load(in_s)  # read the next object from file
                users[o.name] = o  # load the object into the list
            except EOFError:  # We have finished the file
                break  # so we can leave the loop
    theBot.loop.create_task(save_task())
    theBot.loop.create_task(genPower())
    theBot.loop.create_task(update_view())
    return await theBot.change_presence(game=discord.Game(name='Nomic'))


# This section is for custom commands.
@theBot.command(pass_context=True)
async def save(ctx):
    msg = 'Manually saving user data'
    await theBot.say(msg)
    save()


@theBot.command(pass_context=True)
async def info(ctx):
    msg = 'Info: ' + str(ctx.message.channel.server)
    await theBot.say(msg)


@theBot.command(pass_context=True)
async def join(ctx):
    if not str(ctx.message.author) in users:  # if the user isn't already in the list
        users[str(ctx.message.author)] = User(str(ctx.message.author), ctx.message.author.mention)
        msg = '{0.author.mention} has been added to the users list'.format(
            ctx.message)
        await theBot.say(msg)
    else:
        msg = '{0.author.mention} is already in the users list'.format(
            ctx.message)
        await theBot.say(msg)


@theBot.command(pass_context=True)
async def leave(ctx):
    if str(ctx.message.author) in users:  # if the user is already in the list
        users.pop(str(ctx.message.author), None)
        msg = '{0.author.mention} has been removed to the users list'.format(
            ctx.message)
        await theBot.say(msg)
    else:
        msg = '{0.author.mention} is not in the user list'.format(ctx.message)
        await theBot.say(msg)


@theBot.command(pass_context=True)
async def view(ctx):
    msg = ""
    for key, user in users.items():
        msg = msg + str(key) + ": " + str(user.getAttr("watts")) + " watts\n"
    global update_msg  # indicate we want the global variable, not a local
    if msg is not "":
        # send and save the update message
        update_msg = await theBot.send_message(ctx.message.channel, msg)


# Put your other functions here
async def update_view():
    await theBot.wait_until_ready()
    while True:  # set this up as an infinite loop
        if update_msg is not None:  # if we have set a place to update the display
            msg = ""
            for key, user in users.items():
                msg = msg + str(key) + ":\n--Battery: " + str(user.getAttr("watts")) + "/" + str(
                    user.getAttr("battery")) + "W\n--Overflow: " + str(
                    user.getAttr("overflow")) + "W\n\n"
            await theBot.edit_message(update_msg, msg)  # send the edit request
        await asyncio.sleep(update_period)  # wait a specified amount of time


async def genPower():
    await theBot.wait_until_ready()
    while True:
        for key, user in users.items():
            user.addPower()  # This adds the specified number of watts
        await asyncio.sleep(generation_period)


async def save_task():
    await theBot.wait_until_ready()
    while True:
        with open("./data/users.pickle", 'wb') as out_s:  # open the file for writing
            for key, value in users.items():
                pickle.dump(value, out_s)  # write the object to the file
        await asyncio.sleep(save_period)


async def sendMessage(channel, msg):
    await theBot.send_message(channel, msg)


def save():
    with open("./data/users.pickle", 'wb') as out_s:  # open the file for writing
        for key, value in users.items():
            pickle.dump(value, out_s)  # write the object to the file


# These lines MUST be the end of the file. Any code after it might not run properly.
with open("../.token", "r") as myfile:
    data = myfile.read()
theBot.run(data)
