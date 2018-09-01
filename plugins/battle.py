from logging import getLogger
from io import BytesIO
import random

from utils.common import SHIBE_CHANNEL, BATTLE_MSGS, COMMAND_OUTLAWS, REDIRECT_CHANNEL
from utils.db import Database
from utils.deco import ensure_profile, ensure_other, ensure_index, limit_channel

from disco.bot import Plugin
from PIL import Image, ImageDraw, ImageColor
from gevent import sleep, timeout
import requests


class BattlePlug(Plugin):

    def load(self, config):
        self.db = Database("BattlePlug")
        self.shibes = {}
        self.logger = getLogger("BattlePlug")
        super().load(config)
        self.logger.info("Finished loading")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        client = event.guilds[0].client
        shibe_channel = client.api.channels_get(SHIBE_CHANNEL)
        for msg in shibe_channel.messages:
            split_msg = msg.content.split(' ')
            url, name = split_msg[0], ' '.join(split_msg[1:])
            self.shibes[name] = url
        self.logger.info("Finished loading {0} shibes".format(len(self.shibes.keys())))

    @Plugin.command("battle", "<other_user:str> <shibe_index:int>")
    @ensure_profile
    @ensure_index
    @ensure_other
    @limit_channel(*COMMAND_OUTLAWS, alternative_channel_id=REDIRECT_CHANNEL)
    def start_battle(self, event, user, shibe, other_user, shibe_index: int):
        if user.user_id == other_user.user.id:
            return event.msg.reply("You can't battle yourself. That defeats the purpose.")

        event.msg.reply("Hey {0}! <@{1}> has challenged you to a duel! Type !accept if you accept,"
                        " or !decline if you decline.".format(other_user.user.mention, user.user_id))
        other_status = None

        def cond(event):
            nonlocal other_status
            if event.content.startswith("!accept"):
                other_status = True
            elif event.content.startswith("!decline"):
                other_status = False
            else:
                return False
            return True

        result = self.wait_for_event("MessageCreate", conditional=cond,
                                     channel__id=event.msg.channel.id, author__id=other_user.user.id)
        try:
            result.get(timeout=30.0)
        except timeout.Timeout:
            return event.msg.reply("Sorry, but your opponent didn't reply in time. Try someone else!")
        if not other_status:
            return event.msg.reply("Well, that's too bad. I bet you're just scared.")
        event.msg.reply("Alright! And what shibe will you be using {0}? (provide an index, see !inv)"
                        .format(other_user.user.mention))

        def cond(event):
            if event.content.isnumeric():
                return True
            return False

        result = self.wait_for_event("MessageCreate", conditional=cond,
                                     channel__id=event.msg.channel.id,  author__id=other_user.user.id)
        try:
            number = int(result.get(timeout=30.0).content)
        except timeout.Timeout:
            return event.msg.reply("Sorry, but your opponent didn't reply in time. Try someone else!")

        other_user_db = self.db.find_user(other_user.user.id)
        if not other_user_db:
            return event.msg.reply("Sorry, that shibe doesn't exist. Why don't you check again another time?")
        try:
            other_shibe = other_user_db.shibes[number - 1]
        except IndexError:
            return event.msg.reply("Sorry, that shibe doesn't exist. Why don't you check again another time?")
        event.msg.reply("Alright, let's DUEL! (This may take a bit, please be patient :wink:)")

        main_shibe_image = self.shibes[shibe[0]]
        other_shibe_image = self.shibes[other_shibe[0]]
        main_resp = requests.get(main_shibe_image)
        main_image = BytesIO(main_resp.content)
        other_resp = requests.get(other_shibe_image)
        other_image = BytesIO(other_resp.content)
        background = Image.open("imgs/background.jpg")
        main_image = Image.open(main_image).resize((240, 200))
        background.paste(main_image, (500, 250))
        other_image = Image.open(other_image).resize((150, 150))
        background.paste(other_image, (1200, 300))

        main_health, other_health, turn, last_msg = 100, 100, random.randint(0, 1), None
        while main_health > 0 and other_health > 0:
            send_background = background.copy()
            draw_background = ImageDraw.Draw(send_background)
            draw_background.rectangle([(500, 150), (500 + (main_health * 3), 175)], fill=ImageColor.getrgb("green"))
            draw_background.rectangle([(1200, 200), (1200 + (other_health * 3), 175)], fill=ImageColor.getrgb("green"))

            upload_file = BytesIO()
            send_background.save(upload_file, format="png")
            upload_file.seek(0)
            if last_msg:
                new_msg = event.msg.reply(battle_msg, attachments=[("battle.png", upload_file)])
                last_msg.delete()
                last_msg = new_msg
            else:
                last_msg = event.msg.reply("Let's BEGIN!", attachments=[("battle.png", upload_file)])

            if turn % 2:
                main_health -= random.randint(20, 60)
                battle_msg = random.choice(BATTLE_MSGS).format(other_user_db.user_id, other_shibe[0], shibe[0])
            else:
                other_health -= random.randint(15, 50)
                battle_msg = random.choice(BATTLE_MSGS)
                battle_msg = battle_msg.format(user.user_id, shibe[0], other_shibe[0])
            turn += 1

            sleep(1)

        if main_health <= 0:
            main_health, msg = 0, other_user.user.mention + " won! You get <@{0}>'s {1}".format(user.user_id, shibe[0])
        else:
            other_health, msg = 0, "<@{0}> won! You get {1}'s {2}"\
                .format(user.user_id, other_user.user.mention, other_shibe[0])

        send_background = background.copy()
        draw_background = ImageDraw.Draw(send_background)
        draw_background.rectangle([(500, 150), (500 + (main_health * 3), 175)], fill=ImageColor.getrgb("green"))
        draw_background.rectangle([(1200, 200), (1200 + (other_health * 3), 175)], fill=ImageColor.getrgb("green"))

        upload_file = BytesIO()
        send_background.save(upload_file, format="png")
        upload_file.seek(0)
        event.msg.reply(msg, attachments=[("battle.png", upload_file)])
        last_msg.delete()

        if not main_health:
            user.remove_shibe(shibe_index - 1)
            other_user_db.add_shibe(shibe[0])
        else:
            other_user_db.remove_shibe(number - 1)
            user.add_shibe(other_shibe[0])

    @Plugin.command("bestfren")
    def best_friend(self, event):
        person = random.choice([self.shibes["Jack Shibe"], self.shibes["Para Shibe"]])
        resp = requests.get(person)
        file = BytesIO(resp.content)
        event.msg.reply(attachments=[("bestfriend.png", file)])
