from logging import getLogger

from utils.common import GENERAL_CHANNEL
from utils.db import InviteDatabase, Database
from utils.deco import ensure_profile

from disco.api.http import APIException
from disco.bot import Plugin


class InvitePlug(Plugin):

    def load(self, config):
        self.invite_db = InviteDatabase()
        self.db = Database("InvitePlug")
        self.logger = getLogger("InvitePlug")
        super().load(config)
        self.logger.info("Finished loading invite plugin")

    @Plugin.listen("GuildMemberAdd")
    def on_member(self, event):
        if self.invite_db.already_joined(event):
            self.logger.info("User {0} has rejoined the server".format(event.user.id))
        else:
            for invite in self.invite_db:
                try:
                    invite_obj = event.client.api.invites_get(invite['invite_code'])
                    print(invite_obj.uses, "/", invite_obj.max_uses)
                except APIException:
                    self.logger.info("Invite revoked! Rewarding accordingly")
                    self.db.create_user(event.user)
                    invited = self.db.find_user(event.user.id)
                    inviter = self.db.find_user(invite['user_id'])
                    invited.bepis += 20
                    inviter.bepis += 30
                    event.client.api.channels_messages_create(
                        GENERAL_CHANNEL,
                        "Thanks for inviting <@{0}>, <@{1}>. You've earned 30 bepis and"
                        " <@{1}> earned 20 for using the referral link".format(invited.user_id, inviter.user_id)
                    )
                    self.invite_db.remove_invite(invite['invite_code'])
                    self.logger.info("Removed invite and rewarded users")
                    break
            else:
                self.db.create_user(event.user)
            self.logger.info("Created account for User {0}".format(event.user.id))

    @Plugin.command("invite")
    @ensure_profile
    def create_invite(self, event, user):
        invite = self.invite_db.invites.find_one({"user_id": user.user_id})
        if invite:
            invite_code = invite['invite_code']
        else:
            invite = event.msg.channel.create_invite(
                max_age=0,
                max_uses=1,
                unique=True
            )
            invite_code = invite.code
            self.invite_db.register_invite(invite_code, user.user_id)
        event.msg.reply("There! Here's your referral link. Whenever a person joins with this link, you'll get 30 bepis"
                        "and they'll get 20. Make sure to get a new link after inviting someone! https://discord.gg/"
                        + invite_code)
