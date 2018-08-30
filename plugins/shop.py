from logging import getLogger
from random import randint

from utils.common import SHIBE_CHANNEL
from utils.db import Database
from utils.deco import ensure_profile, ensure_other, ensure_index

from disco.bot import Plugin
from disco.types.message import MessageEmbed


class ShopPlug(Plugin):

    def load(self, config):
        self.db = Database("ShopPlug")
        self.logger = getLogger("ShopPlug")
        self.shibes = {}
        super().load(config)
        self.logger.info("Finished loading ShopPlug")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            _, name = split_msg[0], ' '.join(split_msg[1:])
            if "⭐" in name:
                value = 30
            elif "🌟" in name:
                value = 50
            elif "💫" in name:
                value = 100
            else:
                value = 20
            self.shibes[name] = value
        self.shibes = sorted(self.shibes.items(), key=lambda x: x[1])
        self.shibes.reverse()
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes)))

    @Plugin.command("bepis", "[other_user:str]")
    @ensure_profile
    @ensure_other
    def get_bepis(self, event, user, other_user=None):
        if other_user:
            other_db = self.db.find_user(other_user.user.id)
            event.msg.reply("{1} has **{0}** bepis".format(other_db.bepis, other_user.user.username))
        else:
            event.msg.reply("You have **{0}** bepis".format(user.bepis))
        self.logger.info("User {0} is making it rain".format(user.user_id))

    @Plugin.command("sell", "<shibe_index:int>")
    @ensure_profile
    @ensure_index
    def sell_shibe(self, event, user, shibe, shibe_index: int):
        if "⭐" in shibe[0]:
            user.bepis += 20
        elif "🌟" in shibe[0]:
            user.bepis += 40
        elif "💫" in shibe[0]:
            user.bepis += 80
        else:
            user.bepis += 10
        event.msg.reply("Thanks for the {0}, you now have {1} bepis".format(shibe[0], user.bepis))
        index = user.shibes.index(shibe)
        user.remove_shibe(index)

    @Plugin.command("shop", "[page:int]")
    def show_shop(self, event, page: int=1):
        if page not in range(1, (len(self.shibes) // 20) + 2):
            return event.msg.reply("Invalid page number, choose a page from 1 to {0}"
                                   .format((len(self.shibes) // 20) + 1))

        embed = MessageEmbed()
        embed.title = "The Shibe Shop!"
        embed.description = "\n".join(map(lambda x: "{0}): Selling {1} for {2}"
                                          .format(x[0] + ((page - 1) * 20) + 1, x[1][0], x[1][1]),
                                          enumerate(self.shibes[20 * (page - 1):page * 20])))
        embed.color = 0xFFFDD0
        embed.set_footer(text="Like what you see? Buy something! page {0}/{1}"
                         .format(page, (len(self.shibes) // 20) + 1))
        event.msg.reply(embed=embed)

    @Plugin.command("buy", "<shop_index:int>")
    @ensure_profile
    def buy_shop(self, event, user, shop_index: int):
        try:
            buy_shibe = self.shibes[shop_index - 1]
        except IndexError:
            return event.msg.reply("Invalid shop index, check !shop again to see if you typed it right.")
        if user.bepis < buy_shibe[1]:
            return event.msg.reply("Sorry, but you need {0} more bepis".format(buy_shibe[1] - user.bepis))
        user.bepis -= buy_shibe[1]
        user.add_shibe(buy_shibe[0])
        event.msg.reply("Thanks for shopping! here's your **{0}**".format(buy_shibe[0]))
        self.logger.info("User {0} bought a {1}".format(user.user_id, buy_shibe[0]))

    @Plugin.command("donate", "<other_user:str>, <amount:int>")
    @ensure_profile
    @ensure_other
    def donate_bepis(self, event, user, other_user, amount: int):
        if user.bepis < amount:
            return event.msg.reply("You don't have enough bepis to donate that amount")
        elif amount < 1:
            return event.msg.reply("You can't just *give* them no money!")
        db_user = self.db.find_user(other_user.user.id)
        user.bepis -= amount
        db_user.bepis += amount
        event.msg.reply("Done! {0} make sure to say 'Thank you'.".format(other_user.user.mention))

    @Plugin.command("flip", "<amount:int>")
    @ensure_profile
    def flip_bepis(self, event, user, amount: int):
        if user.bepis < amount:
            return event.msg.reply("You don't have enough bepis to bet that amount")
        elif amount < 1:
            return event.msg.reply("What? You can't bet nothing!")

        if randint(0, 1):
            user.bepis += amount
            event.msg.reply("Contratz! You won! You now have {0} bepis".format(user.bepis))
        else:
            user.bepis -= amount
            event.msg.reply("Oh no, you lost... You now have {0} bepis".format(user.bepis))
