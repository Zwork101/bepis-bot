# bepis-bot
A discord bot made for a guild I'm in, worked pretty hard on it and I'm happy how it turned out.

## commands
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

## installation

1. Downloading it with the big green button
2. Unzip it (that wasn't hard now was it)

## Setup

First, the bot uses 2 ENV variables. On a linux based machine, use `export key=value`. On windows, use `set key=value`
1. Fetch the token you plan on using. Do `export/set TOKEN=<discord token>`
2. Fetch your mongodb URI with the user + pass, and do `export/set MONGO_URI=<mongodb uri>`
3. Then, look in utils/common.py, and replace all the IDs to your own server.

Bot should be good to go! It'll create profiles on the mongodb, feel free to make any adjustments you want.

### credits

This bot was made by me, using disco-py (take THAT discord.py fans). Contact me on discord with *Zwack010#5682*
