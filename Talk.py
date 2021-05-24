'''BOT EXTENSION'''
import logging
import operator

import discord
from aioconsole import ainput
from discord.ext import commands

#Logging
LOGGER = logging.getLogger("Bot")

CMDS_LIST = '''
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

NOTE: All commands are case insensitive!'''


def prettylist(items):
    '''
    Takes any objects that have the attributes 'name' and 'id'

    Creates a pretty list in the format:
        AAAAA - AID
        BB    - BID
        CCC   - CID
    '''

    #Calculate max string length
    max_width = max(
        list(
            map(
                len,
                map(
                    operator.attrgetter("name"),
                    items
                )
            )
        )
    )

    #Create template string for format
    template_str = f"{{:<{max_width}}} - {{}}"

    list_str = []

    for item in items:
        list_str.append(template_str.format(item.name, item.id))
    return "\n".join(list_str)


class Talk(commands.Cog, name="ThisShouldNotBeShown"):
    '''class description'''
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.input_loop())


    async def input_loop(self):
        '''Command line interface'''
        LOGGER.debug("Waiting until bot is ready...")
        await self.bot.wait_until_ready()

        #Server and channel
        cur_guild = None
        cur_channel = None

        #Attach something to the next message
        msg_attachment = None

        #Console Input Loop
        LOGGER.info("Console activated! Enter 'HELP' for a list of commands!")
        while True:
            #Display current environment
            loc_str = []

            #Server
            if cur_guild is not None:
                loc_str.append(f"SRV: {getattr(cur_guild, 'name', cur_guild)}")

            #Channel
            if cur_channel is not None:
                loc_str.append(f"CH: {getattr(cur_channel, 'name', cur_channel)}")

            #Attachment
            if msg_attachment is not None:
                loc_str.append(f"ATT: {msg_attachment.filename}")

            loc_str = "; ".join(loc_str)

            #Read input (async)
            try:
                in_str = await ainput(loc_str+"> ")
            except EOFError: #CTRL + D -> Exit
                in_str = "exit"

            in_str = in_str.rstrip(" ")
            in_str_lower = in_str.lower()

            #Process input and commands
            try:
                #Print a list of commands
                if in_str_lower == "help":
                    LOGGER.info("List of commands: %s", CMDS_LIST)

                #Select server
                elif in_str_lower.startswith("srv"):
                    guild_id = int(in_str[4:])

                    tmp_guild = self.bot.get_guild(guild_id)

                    if tmp_guild is None:
                        LOGGER.error("Server not found!")
                    else:
                        cur_guild = tmp_guild
                        LOGGER.info("Server set to %s!", cur_guild.name)

                #Select channel
                elif in_str_lower.startswith("ch"):
                    channel_id = int(in_str[3:])

                    #Get channel by global search
                    if cur_guild is None:
                        LOGGER.info("Fetching channel...")
                        tmp_channel = await self.bot.fetch_channel(channel_id)

                        if not isinstance(tmp_channel, discord.TextChannel):
                            #NOTE: excluding DM channels to prevent malicious use!
                            LOGGER.error("Channel is not a text channel!")
                        else:
                            cur_channel = tmp_channel
                            cur_guild = cur_channel.guild
                            LOGGER.info("Channel set to %s!", cur_channel.name)
                            LOGGER.info("Server set to %s!", cur_guild.name)

                    #Get channel on the specified server
                    else:
                        tmp_channel = cur_guild.get_channel(channel_id)

                        if tmp_channel is None:
                            LOGGER.error("Channel not found on this server!")
                        else:
                            cur_channel = tmp_channel
                            LOGGER.info("Channel set to %s!", cur_channel.name)

                #Add attachment to the next msg
                elif in_str_lower.startswith("file"):
                    if in_str_lower == "file clear": #Clear attachment
                        msg_attachment = None
                        LOGGER.info("Attachment removed!")
                    else:
                        att_url = in_str[5:]

                        #Get file name from URL
                        att_name = att_url.split("/")[-1].split("?")[0]

                        msg_attachment = discord.File(att_url, filename=att_name)
                        LOGGER.info("Added %s as attachment!", att_url)

                #Send message
                elif in_str_lower.startswith("msg"): #Send message
                    if cur_channel is None:
                        LOGGER.error("No channel selected!")
                    else:
                        await cur_channel.send(in_str[4:], file=msg_attachment)
                        msg_attachment = None
                        LOGGER.info("Message sent to channel '%s' on '%s'!",cur_channel.name, cur_guild.name)

                #List stuff
                elif in_str_lower.startswith("ls"):
                    ls_res = in_str_lower[3:]

                    #Auto select
                    if ls_res == "":
                        if cur_guild is None:
                            ls_res = "srv"
                        else:
                            ls_res = "ch"

                    #Server
                    if ls_res == "srv":
                        LOGGER.info("Current guilds: \n%s", prettylist(self.bot.guilds))
                    elif ls_res == "ch":
                        if cur_guild is None:
                            LOGGER.error("No server selected!")
                        else:
                            #Get Channels
                            guild_channels = cur_guild.channels or await cur_guild.fetch_channels()

                            LOGGER.info("Text channels on '%s': \n%s", cur_guild.name, prettylist(
                                        list(
                                            filter(
                                            lambda channel : isinstance(channel, discord.channel.TextChannel),
                                            guild_channels
                                        )
                                    )
                                )
                            )
                    else:
                        LOGGER.error("Unknown resource '%s'!", in_str[3:])

                #Quit Sibelius
                elif in_str_lower == "exit":
                    #Confirm selection
                    try:
                        quit_yn = (await ainput("Exit? [y/N]: ")).lower()
                    except EOFError:
                        quit_yn = "y"

                    #Quit
                    if quit_yn == "y":
                        LOGGER.info("Terminal closed!")
                        break

                #Unknown command
                else:
                    if in_str != "":
                        LOGGER.error("Unknown command '%s'!", in_str)
            except Exception as input_exception:
                LOGGER.error("Error processing user command!", exc_info=input_exception)


def setup(bot):
    '''import and run extension'''
    bot.add_cog(Talk(bot))
