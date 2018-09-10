# from datetime import timedelta, datetime
from random import choice

POWERUP_FRAMES = [
    # ("Shibe Whistle", None, 50, "Reduce the catch wait by 2 hours for 1 day."),
    # ("Super Fun Ball", None, 25, "Decrease the rarity of rare shibes for your next 10 catches."),
    ("Battle Hardened Shibes", True, 100, "Increase your min attack by 4, max 3 powerups. Last forever."),
    ("Dazzling Shibe", None, 50, "Sell your shibes for market value for the next 5 sales."),
    ("Sneaky Trap", None, 40, "Whenever target player does !catch, steal the result. Works only 1 time.")
]


# def check_whistle_power(profile):
#     for powerup in profile.powerups:
#         if powerup[0] == POWERUP_FRAMES[0][0] and powerup[1] is not None:
#             if datetime.now() - powerup[1] > timedelta(days=1):
#                 profile.remove_powerup(powerup[0])
#                 return False
#             return True
#     return False
#
#
# def check_ball_power(profile):
#     for powerup in profile.powerups:
#         if powerup[0] == POWERUP_FRAMES[1][0] and powerup[1] is not None:
#             powerup[1] -= 1
#             if powerup[1] < 1:
#                 profile.remove_powerup(powerup[0])
#             return True
#     return False


def check_battle_power(profile):
    count = 0
    for powerup in profile.powerups:
        if powerup[0] == POWERUP_FRAMES[2][0]:
            if count < 3:
                count += 1
    return count


def check_dazzle_power(profile):
    for powerup in profile.powerups:
        if powerup[0] == POWERUP_FRAMES[3][0] and powerup[1] is not None:
            powerup[1] -= 1
            if powerup[1] < 1:
                return profile.remove_powerup(powerup[0])
            return True
    return False


def check_trap_power(profile):
    trappers = []
    for powerup in profile.powerups:
        if powerup[0] == "TRAPPED":
            trappers.append(powerup[1])
    if not trappers:
        return None
    return choice(trappers)
