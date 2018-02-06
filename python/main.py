# These are the dependecies.
# The bot depends on these to function, hence the name.
# Please do not change these unless you're adding to them, because they can break the bot.
import discord
import asyncio
from discord.ext.commands import Bot
from discord.ext import commands
import platform
import pickle
import math
import datetime
from random import randint


# This section is for global variables
theBot = Bot(description="Squid Nomic bot for Discord", command_prefix="!", pm_help=False)
users = {}
uptime = 0
save_period = 60
update_period = 5
update_msg = None  # Reference to the message to keep updated
watts_sold = 1  # set to something positive to prevend DIV0 errors

price_battery = 100
price_solar = 1000
price_mine = 5000

drain_mine = 2.0

bots_drain_coal = 1
land_rate = 0.00001


# this section is for custom classes
class User():
    def __init__(self, name, mention):
        self.name = name
        self.mention = mention
        self.data = {}

    def getAttr(self, key):  # Get in for for this instance
        if key in self.data:
            return self.data[key]  # get a amount unique
        elif key == 'watts':  # otherwise, the following are default values
            return 0
        elif key == 'batteries':
            return 4
        elif key == 'cash':
            return 0
        elif key == 'mine':
            return 0
        elif key == 'coal':
            return 0
        elif key == 'stone':
            return 0
        elif key == 'copper':
            return 0
        elif key == 'mine_partial':
            return 0
        elif key == 'solar_panels':
            return 1
        elif key == "max_watts":
            return self.getAttr("batteries") * 25
        elif key == 'bots':
            return 0
        elif key == 'land':
            return 0
        else:
            return None  # if we reach this, the requested key was not found

    def setAttr(self, key, value):  # set the value of an attribute of this instance
        self.data[key] = value

    def updatePower(self):
        self.addPower()
        self.runMine()
        self.runBots()

    def runMine(self):
        for f in range(0, self.getAttr('mine')):
            if self.consumePower(drain_mine):
                mined = self.generateOre()
                self.setAttr(mined['type'], self.getAttr(mined['type']) + mined['amount'])
            else:
                remain = self.getAttr("watts")
                self.consumePower(remain)
                self.setAttr("mine_partial", self.getAttr("mine_partial") + remain)
                if self.getAttr("mine_partial") >= drain_mine:
                    self.setAttr("mine_partial", self.getAttr("mine_partial") - drain_mine)
                    mined = self.generateOre()
                    self.setAttr(mined['type'], self.getAttr(mined['type']) + mined['amount'])

    def runBots(self):
        for f in range(0, self.getAttr('bots')):
            if self.consumeCoal(bots_drain_coal):
                self.setAttr('land', land_rate + self.getAttr('land'))

    def generateOre(self):
        weights = [(10, {'type': 'coal', 'amount': 1}),
                   (100, {'type': 'stone', 'amount': 1}),
                   (4, {'type': 'copper', 'amount': 1})
                   ]
        return getWeightedRandom(weights)

    def consumeCoal(self, consumed):  # Attempt to consume coal. Returns True if successful
        if self.getAttr("coal") >= consumed:
            self.setAttr("coal", self.getAttr("coal") - consumed)
            return True
        else:
            return False

    def addPower(self):
        global update_msg
        # how much space is left in the battery
        battery_room = self.getAttr("max_watts") - self.getAttr("watts")
        generated = self.getGenRate()
        if battery_room > 0:
            if battery_room > generated:
                self.setAttr("watts", round(self.getAttr("watts") + generated, 2))
            else:
                if update_msg is not None:
                    msg = self.mention + " has a full battery"
                    # theBot.loop.create_task(sendMessage(update_msg.channel, msg))  # causing spam
                self.setAttr("watts", self.getAttr("max_watts"))

    def consumePower(self, consumed):  # Attempt to consume power. Returns True if successful
        if self.getAttr("watts") >= consumed:
            self.setAttr("watts", self.getAttr("watts") - consumed)
            return True
        else:
            return False

    def gainCash(self, gained):
        self.setAttr("cash", round(self.getAttr("cash") + gained, 2))

    def spendCash(self, spent):
        if self.getAttr("cash") >= spent:
            # spend
            self.setAttr("cash", round(self.getAttr("cash") - spent, 2))
            return True
        return False

    def spendSolar(self, spent):
        if self.getAttr("solar_panels") >= spent:
            # spend
            self.setAttr("solar_panels", round(self.getAttr("solar_panels") - spent, 2))
            return True
        return False

    def getGenRate(self):
        return round(self.getAttr("solar_panels") * getSolarOut(), 2)


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

    with open("./data/general.pickle", 'rb') as in_s:  # open the file for reading
        try:
            global uptime
            uptime = pickle.load(in_s)
            global watts_sold
            watts_sold = pickle.load(in_s)
        except EOFError:  # We have finished the file
            print("Couldn't finish reading file")

    theBot.loop.create_task(save_task())
    theBot.loop.create_task(powerTick())
    theBot.loop.create_task(update_view())
    return await theBot.change_presence(game=discord.Game(name='Nomic'))


# This section is for custom commands.
@theBot.command(pass_context=True, help='purchases stuff. you must have the funds to do so.')
async def buy(ctx):
    msg = "Invalid item"
    user = get_user_or_None(ctx.message.author)
    if user is None:
        msg = "You are not a player, and therefore can't really do anything"
        await theBot.say(msg)
        return
    args = (ctx.message.content).split()
    if len(args) == 1:
        msg = "Please specify something to buy." \
            " Usually this will be in the form of '!buy {thing} {amount}'"
        await theBot.say(msg)
        return
    if len(args) == 2:
        amount = 1
    else:
        try:
            amount = int(args[2])
            if amount <= 0:
                msg = "You can't purchase that amount"
                await theBot.say(msg)
                return
        except ValueError:
            msg = "An invalid amount was supplied. Please make sure it is a whole number."
            await theBot.say(msg)
            return
    # actually do the purchase here.
    if args[1].lower() == "battery":
        price = getPrice(user, "batteries", amount)
        if user.spendCash(price):
            user.setAttr("batteries", user.getAttr("batteries") + amount)
            msg = "You have bought " + str(amount) + " batteries for $" + str(price)
        else:
            msg = "You can't affort that many. It will cost $" + str(price)
    if args[1].lower() == "solar":
        price = getPrice(user, "solar_panels", amount)
        if user.spendCash(price):
            user.setAttr("solar_panels", user.getAttr("solar_panels") + amount)
            msg = "You have bought " + str(amount) + " solar panels for $" + str(price)
        else:
            msg = "You can't afford that many. It will cost $" + str(price)
    if args[1].lower() == "mine":
        price = getPrice(user, "mine", amount)
        if user.spendCash(price):
            user.setAttr("mine", user.getAttr("mine") + amount)
            msg = "You have bought " + str(amount) + " mines for $" + str(price)
        else:
            msg = "You can't afford that many. It will cost $" + str(price)
    await theBot.say(msg)


@theBot.command(pass_context=True, help='build stuff. you must have the funds to do so.')
async def build(ctx):
    msg = "Invalid item"
    user = get_user_or_None(ctx.message.author)
    if user is None:
        msg = "You are not a player, and therefore can't really do anything"
        await theBot.say(msg)
        return
    args = (ctx.message.content).split()
    if len(args) == 1:
        msg = "Please specify something to build." \
            " Usually this will be in the form of '!build {thing} {amount}'"
        await theBot.say(msg)
        return
    if len(args) == 2:
        amount = 1
    else:
        try:
            amount = int(args[2])
            if amount <= 0:
                msg = "You can't build that amount"
                await theBot.say(msg)
                return
        except ValueError:
            msg = "An invalid amount was supplied. Please make sure it is a whole number."
            await theBot.say(msg)
            return
    # actually do the purchase here.
    if args[1].lower() == "bot":
        if user.spendSolar(2 ^ user.getAttr("bots")):
            msg = "You have built a bot out of" + str(2 ^ user.getAttr("bots")) + "solar panels"
            user.setAttr("bots", user.getAttr("bots") + 1)
        else:
            msg = "You can't affort that many"
    await theBot.say(msg)


@theBot.command(pass_context=True, help='Displays basic game info.')
async def info(ctx):
    user = get_user_or_None(ctx.message.author)
    msg = 'Info: \n' + getUserInfo(user)
    msg = msg + "--Resources:\n"
    msg = msg + " * Coal Ore: " + str(user.getAttr("coal")) + "\n"
    msg = msg + " * Copper Ore: " + str(user.getAttr("copper")) + "\n"
    msg = msg + " * Raw Stone: " + str(user.getAttr("stone")) + "\n"
    await theBot.say(msg)


@theBot.command(pass_context=True, help='Attempts to add the sender to the user list')
async def join(ctx):
    if not str(ctx.message.author) in users:  # if the user isn't already in the list
        users[str(ctx.message.author)] = User(str(ctx.message.author), ctx.message.author.mention)
        msg = '{0.author.mention} has been added to the users list'.format(ctx.message)
        await theBot.say(msg)
    else:
        msg = '{0.author.mention} is already in the users list'.format(
            ctx.message)
        await theBot.say(msg)


@theBot.command(pass_context=True, help='Attempts to remove the sender from the user list')
async def leave(ctx):
    if str(ctx.message.author) in users:  # if the user is already in the list
        users.pop(str(ctx.message.author), None)
        msg = '{0.author.mention} has been removed from the users list'.format(ctx.message)
        await theBot.say(msg)
    else:
        msg = '{0.author.mention} is not in the user list'.format(ctx.message)
        await theBot.say(msg)


@theBot.command(pass_context=True, help='Manually saves game data')
async def save(ctx):
    msg = 'Manually saving data'
    await theBot.say(msg)
    save()


@theBot.command(pass_context=True, help='Sell some of your stored power at the current rate')
async def sell(ctx):
    global watts_sold
    user = get_user_or_None(ctx.message.author)
    if user is None:
        msg = "You are not a player, and therefore can't really do anything"
        await theBot.say(msg)
        return
    args = (ctx.message.content).split()
    if len(args) == 1:
        msg = "Please specify an amount to sell (either 'all' or a number)"
        await theBot.say(msg)
        return
    if args[1].lower() == "all":
        # sell all
        watts = user.getAttr("watts")
        price = round(watts * wattPrice(), 2)
        user.consumePower(watts)
        user.gainCash(price)
        watts_sold = watts_sold + watts
        msg = user.mention + " has sold " + str(watts) + "W for $" + str(price)
        await theBot.say(msg)
    else:
        # sell some
        try:
            watts = float(args[1])
            price = round(watts * wattPrice(), 2)
            if watts <= 0:
                msg = "You can't sell a negative amount"
                await theBot.say(msg)
                return
            if user.consumePower(watts):
                user.gainCash(price)
                watts_sold = watts_sold + watts
                msg = user.mention + " has sold " + str(watts) + "W for $" + str(price)
                await theBot.say(msg)
            else:
                msg = "You don't have that much power stored"
                await theBot.say(msg)
        except ValueError:
            msg = "Please specify an amount to sell (either 'all' or a number)"
            await theBot.say(msg)


@theBot.command(pass_context=True, help='Request an auto-updating message')
async def view(ctx):
    msg = ""
    for key, user in users.items():
        msg = msg + getUserInfo(user)
    global update_msg  # indicate we want the global variable, not a local
    if msg is not "":
        # send and save the update message
        update_msg = await theBot.send_message(ctx.message.channel, msg)


# Put your other functions here
def get_user_or_None(member):
    """Checks if a discord user has an associated nomic user"""
    if str(member) in users:
        return users[str(member)]
    else:
        return None


async def powerTick():
    """Function to periodically generate and consume power"""
    global uptime
    await theBot.wait_until_ready()
    while True:
        for key, user in users.items():
            user.updatePower()
        uptime = uptime + 1
        await asyncio.sleep(1)


def getUserInfo(user):
    return str(user.name) + ":\n--Power: " + str(
        user.getAttr("watts")) + "/" + str(
        user.getAttr("max_watts")) + "W\n--Cash: $" + str(
        user.getAttr("cash")) + "\n--W/s: " + str(
        user.getGenRate()) + "\n--Mines: " + str(
        user.getAttr("mine")) + "\n\n"


def getSolarOut():
    hour = (datetime.datetime.now()).hour + (datetime.datetime.now()).minute / 60
    if not (2 < hour < 22):
        return 0
    return round(-0.01 * hour ** 2 + .24 * hour - .44, 2)


def getPrice(user, object, count):
    price_multiplier = 1.05
    current = user.getAttr(object)
    if current is None:
        return None
    if object == "solar_panels":
        price = price_solar
    elif object == "batteries":
        price = price_battery
    elif object == "mine":
        price = price_mine
    for x in range(0, current):
        price = price * price_multiplier
    final_price = 0
    for x in range(0, count):
        price = price * price_multiplier
        final_price = final_price + price
    return round(final_price, 2)


def getWeightedRandom(pairs):
    total = sum(pair[0] for pair in pairs)
    r = randint(1, total)
    for (weight, value) in pairs:
        r -= weight
        if r <= 0:
            return value


async def save_task():
    await theBot.wait_until_ready()
    while True:
        with open("./data/users.pickle", 'wb') as out_s:  # open the file for writing
            for key, value in users.items():
                pickle.dump(value, out_s)  # write the object to the file
        await asyncio.sleep(save_period)


def save():
    with open("./data/users.pickle", 'wb') as out_s:  # open the file for writing user data
        for key, value in users.items():
            pickle.dump(value, out_s)  # write the object to the file

    with open("./data/general.pickle", 'wb') as out_s:  # open the file for writing general data
        pickle.dump(uptime, out_s)  # write the object to the file
        pickle.dump(watts_sold, out_s)


async def sendMessage(channel, msg):
    await theBot.send_message(channel, msg)


async def update_view():
    """Function to send a message update periodically."""
    await theBot.wait_until_ready()
    while True:  # set this up as an infinite loop
        try:
            if update_msg is not None:  # if we have set a place to update the display
                msg = 'Uptime: ' + str(uptime) + "\n$" + str(wattPrice()) + "/W\n\n"
                for key, user in users.items():
                    msg = msg + getUserInfo(user)
                # send the edit request
                await theBot.edit_message(update_msg, msg)
        except:
            print("probably a timeout error here")
        await asyncio.sleep(update_period)  # wait a specified amount of time


def wattPrice():
    """Note: this is effectivly sigmoid(uptime/watts_sold)"""
    return round((1 / (1 + math.exp(-uptime / watts_sold - 1.5))), 4)


# These lines MUST be the end of the file. Any code after it might not run properly.
with open("../.token", "r") as myfile:
    data = myfile.read()
theBot.run(data)
