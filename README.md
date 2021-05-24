# Bot Talk Extension

This extension allows you to send messages as a Discord bot.

## Requirements:

* A Discord Bot using the Discord.py library
* Aioconsole


## Installation

Install the requirements in your bot's environment. (e.g. pipenv)

## Usage

Simply load this extension via [`bot.load_extension`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.load_extension).


## Commands

```
HELP       - Print this info
SRV <id>   - Select the server with the given ID
CH <id>    - Select the channel with the given ID
FILE <url> - Attaches the given file to the next message (Set <url> to 'clear' to clear
MSG <text> - Sends a message containing <text> into the selected channel
LS <res>   - Lists all entries of type <res>
 ├─ LS         - Lists all servers if no server is selected, otherwise lists channels
 ├─ LS SRV     - Lists all servers
 └─ LS CH      - Lists all channels on the current server
EXIT       - Closes the prompt (Does not reopen until restart)
```
**NOTE:** All commands are case insensitive!

## Disclaimer

This extension is not supposed to be used as a replacement for the Discord client and therefore does not display incoming messages.

Additionally, this extension is not able to send direct messages in order to prevent it from being used to spam other users.