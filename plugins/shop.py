from datetime import datetime, timedelta
from logging import getLogger
from random import randint, choice

from utils.common import SHIBE_CHANNEL, LOTTERY_CHANNEL, LOTTERY_ROLE, SHIBE_GUILD
from utils.db import Database, LotteryDatabase
from utils.deco import ensure_profile, ensure_other, ensure_index, admin_only

from disco.bot import Plugin
from disco.types.message import MessageEmbed
import gevent


class ShopPlug(Plugin):

    def load(self, config):
        self.db = Database("ShopPlug")
        self.lottery = LotteryDatabase()
        self.logger = getLogger("ShopPlug")
        self.shibes = {}
        super().load(config)

        self.logger.info("Finished loading ShopPlug")

    def start_lottery(self, client, delay=0):
        gevent.sleep(delay)
        tickets = []
        users = self.lottery.get_users()
        current_lottery = self.lottery.get_event()
        if current_lottery:
            for user in users:
                for _ in range(user['amount']):
                    tickets.append(user["user_id"])
            if not tickets:
                client.api.channels_messages_create(LOTTERY_CHANNEL, "No one bought tickets, so we have no winners.")
            winner = choice(tickets)
            client.api.channels_messages_create(LOTTERY_CHANNEL, "<@&{2}> And the winner is... <@{0}>! Contrats, {1} "
                                                                 "bepis has been added to your account."
                                                .format(winner, current_lottery["value"], LOTTERY_ROLE))
            bepis_user = self.db.find_user(winner)
            bepis_user.bepis += current_lottery["value"]
            guild = client.api.guilds_get(SHIBE_GUILD)
            for member in guild.members.values():
                if LOTTERY_ROLE in member.roles:
                    member.remove_role(LOTTERY_ROLE)

        next_value = randint(100, 200)
        self.lottery.start_lottery(next_value)
        new_lottery = self.lottery.get_event()
        client.api.channels_messages_create(LOTTERY_CHANNEL, "A new lottery has started! Buy tickets with !ticket to "
                                                             "win the ***{0}*** bepis prize! Ends in 12 hours."
                                            .format(new_lottery['value']))
        gevent.spawn_later(new_lottery['length'], self.start_lottery, client)

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        self.shibes = {}
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            _, name = split_msg[0], ' '.join(split_msg[1:])
            if "⭐" in name:
                value = 1000
            elif "🌟" in name:
                value = 10000
            elif "💫" in name:
                continue
            else:
                value = 20
            self.shibes[name] = value
        self.shibes = sorted(self.shibes.items(), key=lambda x: x[1])
        self.shibes.reverse()
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes)))

        current_lottery = self.lottery.get_event()
        if current_lottery:
            delay = datetime.now() - timedelta(seconds=current_lottery['length'])
            if delay >= current_lottery['start_time']:
                self.start_lottery(client)
            else:
                wait = current_lottery['start_time'] - delay
                self.start_lottery(client, wait.seconds)
        else:
            self.start_lottery(client)

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
            user.bepis += 1000
        elif "🌟" in shibe[0]:
            user.bepis += 10000
        elif "💫" in shibe[0]:
            user.bepis += 1000000
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

    @Plugin.command("buy shibe", "<shop_index:int>")
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
        elif user.user_id == other_user.user.id:
            return event.msg.reply("No.")
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

    @Plugin.command("ticket", "<amount:int>")
    @ensure_profile
    def buy_tickets(self, event, user, amount: int):
        current_lottery = self.lottery.get_event()
        if user.bepis < (amount * current_lottery["price"]):
            return event.msg.reply("Sorry, but you don't have enough bepis for that.")
        elif amount <= 0:
            return event.msg.reply("Why are you doing that, that's stupid. Don't be stupid.")
        self.lottery.add_tickets(user.user_id, amount)
        member = event.msg.guild.get_member(user.user_id)
        if LOTTERY_ROLE not in member.roles:
            member.add_role(LOTTERY_ROLE)
        user.bepis -= (amount * current_lottery['price'])
        event.msg.reply("Alright! Added {0} more tickets into your account.".format(amount))

    @Plugin.command("reload shop")
    @admin_only
    def reload_shop(self, event):
        client = event.msg.client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        self.shibes = {}
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            _, name = split_msg[0], ' '.join(split_msg[1:])
            if "⭐" in name:
                value = 1000
            elif "🌟" in name:
                value = 10000
            elif "💫" in name:
                continue
            else:
                value = 20
            self.shibes[name] = value
        self.shibes = sorted(self.shibes.items(), key=lambda x: x[1])
        self.shibes.reverse()
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes)))
        event.msg.reply("Finished reloading shibes. {0} catchable shibes.".format(len(self.shibes.keys())))
