from logging import getLogger

from disco.bot import Plugin

from utils.common import SHIBE_CHANNEL
from utils.db import Database
from utils.deco import admin_only, ensure_other


class AdminPlug(Plugin):

    def load(self, config):
        self.db = Database("AdminPlug")
        self.logger = getLogger("AdminPlug")
        self.shibes = {}
        super().load(config)
        self.logger.info("Finished loading AdminPlug")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
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
