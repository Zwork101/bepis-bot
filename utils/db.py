from asyncio import Task
from datetime import datetime, timedelta
from logging import getLogger
from hashlib import md5
from os import environ
from uuid import uuid4
from threading import Thread
from queue import Queue

from pymongo import mongo_client


class EventHandler(Thread):

    def __init__(self):
        self.q = Queue()
        super().__init__()
        self.start()

    def do(self, command, *args, **kwargs):
        cb = Queue()
        self.q.put((cb, command, args, kwargs))
        return cb.get()

    def run(self):
        while True:
            cb, cmd, args, kwargs = self.q.get()
            cb.put(cmd(*args, **kwargs))


handler = EventHandler()


class BepisUser:

    def __init__(self, name: str, master, contents: dict):
        self.master = master
        self.logger = getLogger(name + "-" + str(contents['user_id']))
        self.user_id = contents['user_id']
        self.shibes = contents['shibes']
        self._bepis = contents['bepis']
        self._last_daily = contents['last_daily']

        if "powerups" not in contents:
            handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"powerups": []}})
            self.powerups = []
        else:
            self.powerups = contents['powerups']

    @property
    def bepis(self):
        return self._bepis

    @bepis.setter
    def bepis(self, value):
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"bepis": value}})
        self._bepis = value
        self.logger.debug("Updated bepis to: " + str(value))

    @property
    def last_daily(self):
        return self._last_daily

    @last_daily.setter
    def last_daily(self, value):
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"last_daily": value}})
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
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"shibes": self.shibes}})
        self.logger.debug("Added shibe: " + shibe_name)

    def remove_shibe(self, shibe_index: int):
        shibe = self.shibes[shibe_index]
        new_count = shibe[1] - 1
        if not new_count:
            self.shibes.pop(shibe_index)
        else:
            self.shibes[shibe_index] = (shibe[0], new_count)
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"shibes": self.shibes}})
        self.logger.debug("Removed shibe: " + shibe[0])

    def add_powerup(self, *data):
        powerups = self.powerups.copy()
        powerups.append(data)
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"powerups": powerups}})
        self.logger.debug("Added powerup: " + powerups[0])

    def remove_powerup(self, name: str):
        for powerup in self.powerups:
            if powerup[0] == name and powerup[1] is not None:
                break
        self.powerups.remove(powerup)
        handler.do(self.master.update_one, {"user_id": self.user_id}, {"$set": {"powerups": powerup}})
        self.logger.debug("Removed powerup: " + powerup[0])


class Database(EventHandler):

    def __init__(self, name: str):
        self.logger = getLogger(name + "-database")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.profiles = self.client['bepis_bot']['profiles']
        self.profiles.create_index("user_id", unique=True)
        super().__init__()

    def create_user(self, user):
        payload = {
            "user_id": user.id,
            "bepis": 0,
            "shibes": [],
            "last_daily": datetime.now() - timedelta(days=1),
            "invite_url": None
        }
        handler.do(self.profiles.insert_one, payload)
        self.logger.debug("Created User: " + str(user.id))
        return BepisUser(self.logger.name, self.profiles, payload)

    def find_user(self, user_id: int):
        prof = handler.do(self.profiles.find_one, {"user_id": user_id})
        if prof:
            self.logger.debug("Found user: " + str(user_id))
            return BepisUser(self.logger.name, self.profiles, prof)
        self.logger.debug("Could not find user: " + str(user_id))


class InviteDatabase(EventHandler):

    def __init__(self):
        self.logger = getLogger("InviteDatabase")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.invites = self.client['bepis_bot']['invites']
        self.profiles = self.client['bepis_bot']['profiles']
        super().__init__()

    def already_joined(self, member):
        user = handler.do(self.profiles.find_one, {"user_id": member.user.id})
        if user is None:
            self.logger.debug("Checking join on {0} (hasn't joined)".format(member.user.id))
            return False
        else:
            self.logger.debug("Checking join on {0} (has joined)".format(member.user.id))
            return True

    def register_invite(self, invite_code: str, user_id: int):
        handler.do(self.invites.insert_one, {
            "invite_code": invite_code,
            "user_id": user_id
        })
        self.logger.debug("Created invite reg for {0}, invite: {1}".format(user_id, invite_code))

    def __iter__(self):
        for invite in self.invites.find({}):
            yield invite

    def remove_invite(self, invite_code: str):
        handler.do(self.invites.delete_one, {"invite_code": invite_code})
        self.logger.debug("Removed invite: {0}".format(invite_code))


class CodeDatabase:

    def __init__(self):
        self.logger = getLogger("CodeDatabase")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.codes = self.client['bepis_bot']['codes']
        self.codes.create_index("hash", unique=True)

    def create_code(self, value: str):
        code = str(uuid4()).upper()
        hashed = md5(code.encode()).hexdigest()
        handler.do(self.codes.insert_one, {"hash": hashed,
                               "value": value})
        return code

    def activate_code(self, code: str):
        hashed = md5(code.encode()).hexdigest()
        result = self.codes.find_one({"hash": hashed})
        if result:
            self.codes.delete_one({"hash": hashed})
            return result['value']


class LotteryDatabase:

    def __init__(self):
        self.logger = getLogger("LotteryDatabase")
        self.client = mongo_client.MongoClient(environ["MONGO_URI"])
        self.lottery = self.client['bepis_bot']['lottery']

    def start_lottery(self, value, length=(5 * 60), price=10):
        handler.do(self.lottery.delete_many, {})
        handler.do(self.lottery.insert_one, {
            "type": "LOTTERY",
            "start_time": datetime.now(),
            "length": length,
            "price": price,
            "value": value
        })

    def add_tickets(self, id: str, amount: int):
        current_amount = handler.do(self.lottery.find_one, {"user_id": id})
        if current_amount:
            total = current_amount["amount"] + amount
            handler.do(self.lottery.update_one, {"user_id": id}, {"$set": {"amount": total}})
        else:
            handler.do(self.lottery.insert_one, {
                "type": "USER",
                "user_id": id,
                "amount": amount
            })

    def get_event(self):
        return handler.do(self.lottery.find_one, {"type": "LOTTERY"})

    def get_users(self):
        return handler.do(self.lottery.find, {"type": "USER"})

