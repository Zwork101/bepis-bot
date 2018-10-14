from logging import getLogger
from io import BytesIO
from traceback import format_exception_only

from disco.bot import Plugin
import requests

from utils.common import SHIBE_CHANNEL, UNCATCHABLE_CHANNEL, BOT_OWNER
from utils.db import Database, CodeDatabase
from utils.deco import admin_only, ensure_other, ensure_profile, ensure_index


class AdminPlug(Plugin):

    def load(self, config):
        self.db = Database("AdminPlug")
        self.code_db = CodeDatabase()
        self.logger = getLogger("AdminPlug")
        self.shibes = {}
        super().load(config)
        self.logger.info("Finished loading AdminPlug")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        for channel_id in (SHIBE_CHANNEL, UNCATCHABLE_CHANNEL):
            shibe_channel = client.api.channels_get(channel_id)
            for msg in shibe_channel.messages:
                split_msg = msg.content.split(' ')
                url, name = split_msg[0], ' '.join(split_msg[1:])
                self.shibes[name] = url
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes.keys())))

    @Plugin.command("set shibe", "<other_user:str> <amount:int> <shibe_name:str...>")
    @ensure_other
    @admin_only
    def set_shibe(self, event, other_user, shibe_name, amount):
        if shibe_name not in self.shibes:
            return event.msg.reply("Sorry, but that shibe doesn't exist (caps sensitive)")
        other_user_db = self.db.find_user(other_user.user.id)
        other_user_db.add_shibe(shibe_name, amount)
        event.msg.reply("Set {0}'s {1} count to {2}".format(other_user.user.mention, shibe_name, amount))
        self.logger.info("Set {0}'s {1} count to {2}".format(other_user.user.id, shibe_name, amount))

    @Plugin.command("set bepis", "<other_user:str> <amount:int>")
    @ensure_other
    @admin_only
    def set_bepis(self, event, other_user, amount: int):
        other_user_db = self.db.find_user(other_user.user.id)
        other_user_db.bepis = amount
        event.msg.reply("Set {0}'s bepis to {1}".format(other_user.user.mention, amount))
        self.logger.info("Set {0}'s bepis to {1}".format(other_user.user.id, amount))

    @Plugin.command("gencode", "<shibe_name:str...>")
    @admin_only
    def create_code(self, event, shibe_name: str):
        if shibe_name not in self.shibes:
            return event.msg.reply("Cannot find shibe: " + shibe_name)
        code = self.code_db.create_code(shibe_name)
        event.msg.reply("Done! The code is " + code)

    @Plugin.command("redeem", "<code:str>")
    @ensure_profile
    def redeem_code(self, event, user, code: str):
        found = self.code_db.activate_code(code)
        if found:
            user.add_shibe(found)
            resp = requests.get(self.shibes[found])
            file = BytesIO(resp.content)
            file.seek(0)
            event.msg.reply("That code was worth a **{}**".format(found), attachments=[(found + ".png", file)])
        else:
            event.msg.reply("Sorry, but that code is invalid.")

    @Plugin.command("eval", "<code:str...>")
    @ensure_profile
    def eval_code(self, event, user, code: str):
        if event.msg.author.id == BOT_OWNER:
            try:
                client = event.guilds[0].client
                returns = str(eval(code, {"event": event, "self": self, "user": user, 'client': client}))
                if len(returns) > 1994:
                    while len(returns) > 1994:
                        to_send = '```' + returns[1994:] + '```'
                        returns = returns[1994:]
                        event.msg.reply(to_send)
                    event.msg.reply('```' + returns + '```')
                else:
                    event.msg.reply('```' + returns + '```')
            except Exception as e:
                returns = '```' + '\n'.join(format_exception_only(type(e), e)) + '```'
                event.msg.reply(returns)
        else:
            event.msg.reply("Did you really think I'd let you do that?")

    @Plugin.command("reload admin")
    def reload_admin(self, event):
        client = event.guilds[0].client
        for channel_id in (SHIBE_CHANNEL, UNCATCHABLE_CHANNEL):
            shibe_channel = client.api.channels_get(channel_id)
            for msg in shibe_channel.messages:
                split_msg = msg.content.split(' ')
                url, name = split_msg[0], ' '.join(split_msg[1:])
                self.shibes[name] = url
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes.keys())))

    # I'm sure you're probobly wondering
    # why the show command is in the admin plugin
    # and that's a great question.
    # So, due to the design of how loading shibes works
    # each plug has it's own copy of shibes
    # the admin plug however, also loads the uncatchable shibes, while shibe_update doesn't.
    # This means that if the show command was where it was supposed to be, it couldn't show uncatchable shibes.
    # As I'm writing this, I've also just realized that I need to load uncatchables for the battle plug.

    @Plugin.command("show", "<shibe_index:int>")
    @ensure_profile
    @ensure_index
    def show_shibe(self, event, user, shibe, shibe_index: int):
        for name, url in self.shibes.items():
            if name == shibe[0]:
                break
        resp = requests.get(url)
        file = BytesIO(resp.content)
        file.seek(0)
        event.msg.reply("Here's your **{0}**".format(shibe[0]), attachments=[(shibe[0] + ".png", file)])
        self.logger.info("User {0} is bragging about his {1}".format(user.user_id, shibe[0]))
