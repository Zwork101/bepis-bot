from functools import wraps


def ensure_profile(func):
    @wraps(func)
    def wrapper(self, event, *args, **kwargs):
        user = self.db.find_user(event.msg.author.id)
        if not user:
            user = self.db.create_user(event.msg.author)
        return func(self, event, user=user, *args, **kwargs)
    return wrapper


def ensure_bepis(amount: int):
    def func_wrapper(func):
        @wraps(func)
        def wrapper(self, event, *args, **kwargs):
            user = self.db.find_user(event.msg.author.id)
            if user.bepis < amount:
                event.msg.reply("Sorry, you don't have enough bepis for this command. You have {0}, while you need {1}"
                                .format(user.bepis, amount))
                return
            return func(self, event *args, **kwargs)
        return wrapper
    return func_wrapper


def ensure_index(func):
    @wraps(func)
    def wrapper(self, event, user, *args, shibe_index: int, **kwargs):
        if shibe_index < 1:
            return event.msg.reply("The index has to be greater than 0")
        try:
            shibe = user.shibes[shibe_index - 1]
        except IndexError:
            event.msg.reply("Sorry, but that shibe doesn't exist.")
            self.logger.warning("User {0} tries to trade index that doesn't exist: {1}".
                                format(user.user_id, shibe_index))
        else:
            return func(self, event, user=user, shibe=shibe, *args, shibe_index=shibe_index, **kwargs)
    return wrapper


def ensure_other(func):
    @wraps(func)
    def wrapper(self, event, *args, other_user: str=None, **kwargs):
        if other_user is not None:
            try:
                if "!" in other_user:
                    actual = event.msg.channel.guild.get_member(other_user[3:-1])
                else:
                    actual = event.msg.channel.guild.get_member(other_user[2:-1])
                if actual is None:
                    raise ValueError("Invalid user")
            except ValueError:
                return event.msg.reply("Invalid mention, who even is that?")
            else:
                other_user = self.db.find_user(actual.user.id)
                if not other_user:
                    self.db.create_user(actual.user)
        return func(self, event, *args,
                    other_user=actual if other_user is not None else other_user, **kwargs)
    return wrapper


def limit_channel(*channel_ids, alternative_channel_id: int=None):
    def wrap_func(func):
        @wraps(func)
        def wrapper(self, event, *args, **kwargs):
            if event.msg.channel.id in channel_ids:
                if alternative_channel_id:
                    event.msg.reply("Sorry, but you can't use that command here. Use <#{0}>"
                                    .format(alternative_channel_id))
                else:
                    event.msg.reply("Sorry, but you can't use that command here.")
            else:
                return func(self, event, *args, **kwargs)
        return wrapper
    return wrap_func
