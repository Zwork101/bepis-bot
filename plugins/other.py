from datetime import datetime

from utils.common import ADDABLE_ROLES

from disco.bot import Plugin
from disco.types.message import MessageEmbed


class ExtraPlug(Plugin):

    @Plugin.command("ping")
    def ping(self, event):
        now = datetime.utcnow()
        offset = now - event.msg.timestamp
        event.msg.reply("Pong! {0}ms".format(offset.microseconds // 1000))

    @Plugin.command("help")
    def help(self, event):
        embed = MessageEmbed()
        embed.title = "Bepis Boi's commands"
        embed.description = """Here are my commands:
***Shibe Commands***
**catch** | Find a random shibe, and add it to your inventory.
**inv** [#] | Look at your collection of shibes, always stored in stacks.
**show** <ID> | Show off your shibes, how cute they are.
**trade** <@> <ID> | Move your shibe into anther person's inventory.
**release** <ID> | Send your shibe off, into the wild.

***Shop Commands***
**bepis** [@] | Admire your bepis, or make fun of someone else's.
**sell** <ID> | Sell one of your shibes. Don't worry, they're in good hands.
**shop** [#] | Look at our large inventory of shibes, you know you want too.
**buy** <ID> | Buy a shibe from our shop. It's worth every bepis.
**donate** <@> <#> | Feeling charitable? Donate bepis to someone else.
**flip** <#> | Flip a coin. You win, double your bet. Lose, lose your bet.

***Fun Commands***
*The following commands don't take any arguments, and show images / videos.*
**disrespect, tarnation, anthem, drincc, pat, politics, soviet, stop,
approved, extreme, no, blank, shibe.**

***Extra Commands***
**invite** | Create an invite link, and share it with your friends to earn bepis.
**battle** <@> <ID> | Challenge someone to a duel, pick shibes, winner get's the loser's shibe.
**ping** | Pong.
**help** | You're looking at it.
**role** <ABC> | Add a sweet role to your account, so people know they're not alone.
**unrole** <ABC> | Remove a previously added role from your account, yw.
**source** | I had to prove the battle cmd wasn't rigged some how.

***Shibe Manager***
*The following commands require the Shibe Manager role*
**set** <@> <#> <ABC> | Set a certain amount of a shibe to someone
**reload** <catch/shrine> | When a new image is added, reload the bot's img cache.
"""
        embed.set_footer(text="<>: required, []: optional, @: mention, "
                              "#: number, ID: shop ID / inventory ID, ABC: text")
        embed.color = 0x000080
        event.msg.reply(embed=embed)

    @Plugin.command("role", "<role_name:str>")
    def add_role(self, event, role_name: str):
        for role in event.msg.channel.guild.roles.values():
            if role.id in ADDABLE_ROLES and role.name.lower() == role_name.lower():
                guild_member = event.msg.channel.guild.get_member(event.msg.author)
                guild_member.add_role(role)
                event.msg.reply("I added **{0}** to your list of roles".format(role.name))
                break
        else:
            event.msg.reply("I could not find the role called {0}".format(role_name))

    @Plugin.command("unrole", "<role_name:str...>")
    def remove_role(self, event, role_name: str):
        guild_member = event.msg.channel.guild.get_member(event.msg.author)
        for role_id in guild_member.roles:
            if role_id in ADDABLE_ROLES:
                real_role = event.channel.guild.roles[role_id]
                if role_name.lower() == real_role.name.lower():
                    guild_member.remove_role(real_role)
                    event.msg.reply("Removed the **{0}** role from you, yw".format(role_name))
                    break
        else:
            event.msg.reply("Couldn't find the **{0}** role on you. Typo?".format(role_name))
