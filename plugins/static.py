from io import BytesIO
from logging import getLogger
from random import choice

from utils.common import SHRINE_CHANNEL
from utils.deco import admin_only

from disco.bot import Plugin
import requests
user_dict = {"para": "https://cdn.discordapp.com/avatars/163657657935200256/b4cca845ea334b4c3b4d40e5bbeafb66.png?size=128",
            "invert": "https://cdn.discordapp.com/avatars/251395704591876096/e9720034c9e3e5ec74cfe56f5cb19f9a.png?size=128",
            "programmer": "https://cdn.discordapp.com/avatars/473977899599396865/2945a2129a43915b6821d9c83549e51d.png?size=128",
            "shannon": "https://media.discordapp.net/attachments/447172845357891596/496048322801434626/Shannon_Shibe.png?width=398&height=301,
            "toxic": "https://media.discordapp.net/attachments/447172845357891596/496048443119370250/Bootiful_Estonian_Sing_Shibe.png?width=327&height=301",
            "shoe":"https://media.discordapp.net/attachments/447172845357891596/496048538602569730/aFineShibe.png?width=359&height=301",
            "jack":"https://media.discordapp.net/attachments/447172845357891596/496048768580321294/Jack_Shibe.png?width=400&height=294"}

class StaticDataPlug(Plugin):

    def load(self, config):
        self.logger = getLogger("StaticDataPlug")
        self.shibes = []
        super().load(config)
        self.logger.info("Finished loading StaticDataPlug")

    @Plugin.listen("Ready")
    def on_ready(self, event):
        channel = event.client.api.channels_get(SHRINE_CHANNEL)
        for msg in channel.messages:
            if msg.content:
                self.shibes.append(("LINK", msg.content))
            elif msg.attachments:
                for attach in msg.attachments.values():
                    self.shibes.append(("ATTACH", attach.url, attach.filename))
        self.logger.info("Loaded images from the shrine, {0}".format(len(self.shibes)))

    @Plugin.command("disrespect")
    def show_disrespect(self, event):
        with open("imgs/disrespect.jpg", "rb") as file:
            event.msg.reply(attachments=[("disrespect.jpg", file)])

    @Plugin.command("tarnation")
    def show_tarnation(self, event):
        with open("imgs/tarnation.jpg", "rb") as file:
            event.msg.reply(attachments=[("tarnation.jpg", file)])

    @Plugin.command("anthem")
    def show_anthem(self, event):
        with open("imgs/anthem.mp4", "rb") as file:
            event.msg.reply(attachments=[("anthem.mp4", file)])

    @Plugin.command("drincc")
    def show_drincc(self, event):
        with open("imgs/drincc.png", "rb") as file:
            event.msg.reply(attachments=[("drinnc.png", file)])

    @Plugin.command("pat")
    def show_pat(self, event):
        with open("imgs/pat.png", "rb") as file:
            event.msg.reply(attachments=[("pat.png", file)])

    @Plugin.command("politics")
    def show_politics(self, event):
        with open("imgs/politics.png", "rb") as file:
            event.msg.reply(attachments=[("politics.png", file)])

    @Plugin.command("soviet")
    def show_soviet(self, event):
        with open("imgs/soviet.png", "rb") as file:
            event.msg.reply(attachments=[("soviet.png", file)])

    @Plugin.command("stop")
    def show_stop(self, event):
        with open("imgs/stop.png", "rb") as file:
            event.msg.reply(attachments=[("stop.png", file)])

    @Plugin.command("approved")
    def show_approved(self, event):
        with open("imgs/approved.png", "rb") as file:
            event.msg.reply(attachments=[("approved.png", file)])

    @Plugin.command("extreme")
    def show_extreme(self, event):
        with open("imgs/extreme.png", "rb") as file:
            event.msg.reply(attachments=[("extreme.png", file)])

    @Plugin.command("no")
    def show_no(self, event):
        with open("imgs/no.png", "rb") as file:
            event.msg.reply(attachments=[("no.png", file)])

    @Plugin.command("blank")
    def show_blank(self, event):
        with open("imgs/....png", "rb") as file:
            event.msg.reply(attachments=[("blank.png", file)])
 
    @Plugin.command("shibe", "[user:str]")
    def random_shibe(self, event, user:str=None):
        if user_dict.get(user) != None :
            event.msg.reply(user_dict.get(user))
            return
        shibe = choice(self.shibes)
        if shibe[0] == "LINK":
            event.msg.reply(shibe[1])
        elif shibe[0] == "ATTACH":
            resp = requests.get(shibe[1])
            file = BytesIO(resp.content)
            file.seek(0)
            event.msg.reply(attachments=[(shibe[2], file)])

    @Plugin.command("source")
    def show_github(self, event):
        event.msg.reply("Read it like the bible: https://github.com/Zwork101/bepis-bot")
    @Plugin.command("reload shrine")
    @admin_only
    def reload_shrine(self, event):
        self.shibes = []
        channel = event.msg.client.api.channels_get(SHRINE_CHANNEL)
        for msg in channel.messages:
            if msg.content:
                self.shibes.append(("LINK", msg.content))
            elif msg.attachments:
                for attach in msg.attachments.values():
                    self.shibes.append(("ATTACH", attach.url, attach.filename))
        self.logger.info("Loaded images from the shrine, {0}".format(len(self.shibes)))
        event.msg.reply("Loaded images from the shrine, {0}".format(len(self.shibes)))

    @Plugin.command("gethapp")
    def get_happy(self, event):
        event.msg.reply("https://cdn.discordapp.com/attachments/442853085639868417/484151984912465941/ZRZafj6h.png")
