from datetime import datetime, timedelta
from logging import getLogger
from os import environ

from pymongo import mongo_client


class BepisUser:

    def __init__(self, name: str, master, contents: dict):
        self.master = master
        self.logger = getLogger(name + "-" + str(contents['user_id']))
        self.user_id = contents['user_id']
        self.shibes = contents['shibes']
        self._bepis = contents['bepis']
        self._last_daily = contents['last_daily']

    @property
    def bepis(self):
        return self._bepis

    @bepis.setter
    def bepis(self, value):
        self.master.update_one({"user_id": self.user_id}, {"$set": {"bepis": value}})
        self._bepis = value
        self.logger.debug("Updated bepis to: " + str(value))

    @property
    def last_daily(self):
        return self._last_daily

    @last_daily.setter
    def last_daily(self, value):
        self.master.update_one({"user_id": self.user_id}, {"$set": {"last_daily": value}})
        self._last_daily = value
        self.logger.debug("Updated last_daily to now")

    def add_shibe(self, shibe_name: str, amount: int=None):
        for i, shibe in enumerate(self.shibes):
            if shibe[0] == shibe_name:
                shibe_amount = (shibe[1] + 1) if amount is None else amount
                self.shibes[i] = shibe_name, shibe_amount
                break
        else:
            self.shibes.append((shibe_name, (1 if amount is None else amount)))
        self.master.update_one({"user_id": self.user_id}, {"$set": {"shibes": self.shibes}})
        self.logger.debug("Added shibe: " + shibe_name)

    def remove_shibe(self, shibe_index: int):
        shibe = self.shibes[shibe_index]
        new_count = shibe[1] - 1
        if not new_count:
            self.shibes.pop(shibe_index)
        else:
            self.shibes[shibe_index] = (shibe[0], new_count)
        self.master.update_one({"user_id": self.user_id}, {"$set": {"shibes": self.shibes}})
        self.logger.debug("Removed shibe: " + shibe[0])


class Database:

    def __init__(self, name: str):
        self.logger = getLogger(name + "-database")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.profiles = self.client['bepis_bot']['profiles']
        self.profiles.create_index("user_id", unique=True)

    def create_user(self, user):
        payload = {
            "user_id": user.id,
            "bepis": 0,
            "shibes": [],
            "last_daily": datetime.now() - timedelta(days=1),
            "invite_url": None
        }
        self.profiles.insert_one(payload)
        self.logger.debug("Created User: " + str(user.id))
        return BepisUser(self.logger.name, self.profiles, payload)

    def find_user(self, user_id: int):
        prof = self.profiles.find_one({"user_id": user_id})
        if prof:
            self.logger.debug("Found user: " + str(user_id))
            return BepisUser(self.logger.name, self.profiles, prof)
        self.logger.debug("Could not find user: " + str(user_id))


class InviteDatabase:

    def __init__(self):
        self.logger = getLogger("InviteDatabase")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.invites = self.client['bepis_bot']['invites']
        self.profiles = self.client['bepis_bot']['profiles']

    def already_joined(self, member):
        user = self.profiles.find_one({"user_id": member.user.id})
        if user is None:
            self.logger.debug("Checking join on {0} (hasn't joined)".format(member.user.id))
            return False
        else:
            self.logger.debug("Checking join on {0} (has joined)".format(member.user.id))
            return True

    def register_invite(self, invite_code: str, user_id: int):
        self.invites.insert_one({
            "invite_code": invite_code,
            "user_id": user_id
        })
        self.logger.debug("Created invite reg for {0}, invite: {1}".format(user_id, invite_code))

    def __iter__(self):
        for invite in self.invites.find({}):
            print(invite)
            yield invite

    def remove_invite(self, invite_code: str):
        self.invites.delete_one({"invite_code": invite_code})
        self.logger.debug("Removed invite: {0}".format(invite_code))
