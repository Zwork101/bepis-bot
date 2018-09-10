from datetime import datetime, timedelta
from logging import getLogger

from utils.db import Database
from utils.deco import ensure_profile, ensure_other
from utils.powers import POWERUP_FRAMES

from disco.bot import Plugin
from disco.types.message import MessageEmbed


class PowerupPlug(Plugin):

    def load(self, config):
        self.db = Database("PowerupPlug")
        self.logger = getLogger("PowerupPlug")
        super().load(config)
        self.logger.info("Finished loading PowerupPlug")

    @Plugin.command("powerups")
    def show_powerup_shop(self, event):
        embed = MessageEmbed()
        embed.title = "Powerup Shop"
        embed.description = "\n\n".join(map(lambda x: "{3}) **{0}** | *{1} bepis*\n***{2}***"
                                            .format(x[1][1], x[1][2], x[1][3], x[0]), enumerate(POWERUP_FRAMES)))
        embed.color = 0xFDB813
        embed.set_footer(text="Don't forget, Battle Hardended Shibes doesn't need to be activated, and Sneaky Trap "
                              "requires a mention for it's target when activating.")
        event.msg.reply("If you buy something, use !activate <ID> when you're ready to use it.", embed=embed)

    @Plugin.command("buy powerup", "<power_index:int>")
    @ensure_profile
    def buy_powerup(self, event, user, power_index: int):
        real_index = power_index - 1
        if real_index < 0 or real_index > len(POWERUP_FRAMES) - 1:
            return event.msg.reply("Sorry, but that powerup does not exist")
        power = POWERUP_FRAMES[real_index]
        if user.bepis < power[2]:
            return event.msg.reply("Sorry, but you don't have enough bepis to buy that.")
        user.bepis -= power[2]
        user.add_powerup(power[0], power[1])

    @Plugin.command("activate", "<power_index:int> [other_user:str]")
    @ensure_profile
    @ensure_other
    def start_powerup(self, event, user, power_index: int, other_user=None):
        real_index = power_index - 1
        if real_index < 0 or real_index > len(user.powerups) - 1:
            return event.msg.reply("Sorry, but you don't have that powerup.")
        power = user.powerups.pop(real_index)
        if power[1] is not None:
            return event.msg.reply("Sorry, but this powerup is already active")
        if power[0] == "Dazzling Shibe":
            power[1] = 5
        elif power[0] == "Sneaky Trap":
            if not other_user:
                return event.msg.reply("You must mention the target person, that you're trapping.")
            db_other = self.db.find_user(other_user.id)
            db_other.add_powerup(("TRAPPED", db_other.user_id))
            power[1] = True
        user.powerups.insert(real_index, power)
        self.db.profiles.update_one({"user_id": user.user_id}, {"$set": {"powerups": user.powerups}})

    @Plugin.command("abilities")
    @ensure_profile
    def show_powerups(self, event, user):
        parsed_powers = []
        for power in user.powerups:
            if type(power[1]) is datetime:
                if datetime.now() - power[1] < timedelta(days=1):
                    diff = datetime.now() - power[1]
                    h, m, s = map(int, str(diff).split(':'))
                    parsed_powers.append("{0}, Active, {1}h {2}m and {3}s left.".format(power[0], h, m, s))
            elif type(power[1]) is int:
                pass  # WIP
            parsed_powers.append()
