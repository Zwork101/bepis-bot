from datetime import datetime, timedelta
from io import BytesIO
from logging import getLogger
from random import choice, randint

from utils.common import SHIBE_CHANNEL, ADD_SHIBE_ROLE, REDIRECT_CHANNEL, COMMAND_OUTLAWS
from utils.db import Database
from utils.deco import ensure_profile, ensure_index, ensure_other, limit_channel, admin_only

import requests
from disco.bot import Plugin
from disco.types.message import MessageEmbed


class ShibeUpdatePlug(Plugin):

    def load(self, config):
        self.db = Database("ShibeUpdatePlug")
        self.logger = getLogger("ShibeUpdatePlug")
        self.shibes = {}
        super().load(config)
        self.logger.info("Finished loading ShibeUpdatePlug")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            url, name = split_msg[0], ' '.join(split_msg[1:])
            self.shibes[name] = url
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes.keys())))

    @Plugin.command("catch")
    @ensure_profile
    @limit_channel(*COMMAND_OUTLAWS, alternative_channel_id=REDIRECT_CHANNEL)
    def catch_chibe(self, event, user):
        diff = datetime.now() - user.last_daily
        if diff >= timedelta(hours=3):
            while True:
                name, url = choice(tuple(self.shibes.items()))
                if "⭐" in name:
                    if randint(1, 100) != 1:
                        continue
                elif "🌟" in name:
                    if randint(1, 500) != 1:
                        continue
                elif "💫" in name:
                    if randint(1, 1000) != 1:
                        continue

                resp = requests.get(url)
                file = BytesIO(resp.content)
                file.seek(0)
                event.msg.reply("You found a **{0}**".format(name), attachments=[(name + ".png", file)])
                user.add_shibe(name)
                user.last_daily = datetime.now()
                self.logger.info("User {0} caught a {1}".format(user.user_id, name))
                break
        else:
            hours, minutes, seconds = map(lambda x: int(float(x)), str(diff).split(':'))
            print(hours, minutes, seconds)
            return event.msg.reply(
                "Sorry, you still have to wait {0} hours, {1} minutes, and {2} seconds."
                .format(2 - hours, 59 - minutes, 59 - seconds))

    @Plugin.command("inv", "[page:int]")
    @ensure_profile
    @limit_channel(*COMMAND_OUTLAWS, alternative_channel_id=REDIRECT_CHANNEL)
    def list_shibes(self, event, user, page: int=1):
        if not user.shibes:
            event.msg.reply("You don't have any shibes. Type !catch to find one.")
        else:
            if page < 1:
                return event.msg.reply("Sorry, you'll need to choose a positive number")
            selected = user.shibes[20 * (page - 1):page * 20]
            if not selected:
                return event.msg.reply("Sorry, but that page doesn't exist")

            embed = MessageEmbed()
            embed.title = event.msg.author.username + "'s shibes"
            embed.description = "\n".join(map(lambda x: "{0}): {1} x {2}"
                                              .format(user.shibes.index(x) + 1, x[0], x[1]), selected))
            embed.color = 0x0ddb93
            embed.set_footer(text="Nice shibes! page {0}/{1}".format(page, (len(user.shibes) // 20) + 1))
            event.msg.reply(embed=embed)
            self.logger.info("User {0} is counting his shibe".format(user.user_id))

    @Plugin.command("trade", "<other_user:str> <shibe_index:int>")
    @ensure_profile
    @ensure_index
    @ensure_other
    def trade_shibe(self, event, user, shibe, other_user, shibe_index: int):
        if other_user.user.id == user.user_id:
            return event.msg.reply("You can't trade with yourself, that's silly. Don't do silly things.")
        other_profile = self.db.find_user(other_user.user.id)
        other_profile.add_shibe(shibe[0])
        user.remove_shibe(shibe_index - 1)
        self.logger.info("Finished trade for {0}: {1} -> {2}"
                         .format(shibe[0], event.msg.author.username, other_user.user.username))
        event.msg.reply("Done! Enjoy your shibes!")

    @Plugin.command("release", "<shibe_index:int>")
    @ensure_profile
    @ensure_index
    def release_shibe(self, event, user, shibe, shibe_index: int):
        user.remove_shibe(shibe_index - 1)
        event.msg.reply("Now there's one more {0} in the wild".format(shibe[0]))
        self.logger.info("User {0} released their {1}".format(user.user_id, shibe[0]))

    @Plugin.command("reload catch")
    @admin_only
    def reload_shibes(self, event):
        client = event.msg.client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        self.shibes = {}
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            url, name = split_msg[0], ' '.join(split_msg[1:])
            self.shibes[name] = url
        self.logger.info("Finished reloading {0} shibes".format(len(self.shibes.keys())))
        event.msg.reply("Finished reloading shibes. {0} catchable shibes.".format(len(self.shibes.keys())))
