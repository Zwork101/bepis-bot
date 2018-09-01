from datetime import datetime, timedelta
from io import BytesIO
from logging import getLogger
from random import choice, randint

from utils.common import SHIBE_CHANNEL, ADD_SHIBE_ROLE, REDIRECT_CHANNEL, COMMAND_OUTLAWS
from utils.db import Database
from utils.deco import ensure_profile, ensure_index, ensure_other, limit_channel

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
        if diff > timedelta(hours=3):
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
            hours, remainder = divmod(diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)  # Thanks stackoverflow
            return event.msg.reply(
                "Sorry, you still have to wait {0} hours, {1} minutes, and {0} seconds"
                .format(hours - 1, minutes, seconds))

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

    @Plugin.command("trade", "<other_user:str> <shibe_index:int>")
    @ensure_profile
    @ensure_index
    @ensure_other
    def trade_shibe(self, event, user, shibe, other_user, shibe_index: int):
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

    @Plugin.command("set", "<other_user:str> <amount:int> <shibe_name:str...>")
    @ensure_other
    def add_shibe(self, event, other_user, shibe_name, amount):
        shibe_name = shibe_name.replace(":star:", "⭐")
        shibe_name = shibe_name.replace(":star2:", "🌟")
        shibe_name = shibe_name.replace(":dizzy:", "💫")

        guild_member = event.msg.channel.guild.get_member(event.msg.author)
        if ADD_SHIBE_ROLE not in guild_member.roles:
            return event.msg.reply("Sorry, but you can't do that.")
        elif shibe_name not in self.shibes:
            return event.msg.reply("Sorry, but that shibe doesn't exist (caps sensitive)")
        other_user_db = self.db.find_user(other_user.user.id)
        other_user_db.add_shibe(shibe_name, amount)
        event.msg.reply("Set {0}'s {1} count to {2}".format(other_user.user.mention, shibe_name, amount))
        self.logger.info("Set {0}'s {1} count to {2}".format(other_user.user.mention, shibe_name, amount))
