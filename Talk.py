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
    SEND_EMBED - Sends an embed into the channel (interactive)
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
        self.current_guild = None
        self.current_channel = None

        #Attach something to the next message
        self.current_attachment = None

        #Console Input Loop
        LOGGER.info("Console activated! Enter 'HELP' for a list of commands!")
        while True:
            #Display current environment
            loc_str = []

            #Server
            if self.current_guild is not None:
                loc_str.append(f"SRV: {getattr(self.current_guild, 'name', self.current_guild)}")

            #Channel
            if self.current_channel is not None:
                loc_str.append(f"CH: {getattr(self.current_channel, 'name', self.current_channel)}")

            #Attachment
            if self.current_attachment is not None:
                loc_str.append(f"ATT: {self.current_attachment.filename}")

            loc_str = "; ".join(loc_str)

            #Read input (async)
            try:
                in_str = await ainput(f"{loc_str}> ")
            except EOFError: #CTRL + D -> Exit
                in_str = "exit"

            if await self.eval_user_command(in_str):
                LOGGER.info("Prompt closed!")
                break


    async def eval_user_command(self, command_str: str) -> bool:
        command_str = command_str.rstrip(" ")
        in_str_lower = command_str.lower()

        # Process input and commands
        try:
            # Print a list of commands
            if in_str_lower == "help":
                LOGGER.info("List of commands: %s", CMDS_LIST)
                return

            # Select server
            if in_str_lower.startswith("srv"):
                guild_id = int(command_str[4:])

                tmp_guild = self.bot.get_guild(guild_id)

                if tmp_guild is None:
                    LOGGER.error("Server not found!")
                    return

                self.current_guild = tmp_guild
                LOGGER.info("Server set to %s!", self.current_guild.name)
                return

            # Select channel
            if in_str_lower.startswith("ch"):
                channel_id = int(command_str[3:])

                #Get channel by global search
                if self.current_guild is None:
                    LOGGER.info("Fetching channel...")
                    tmp_channel = await self.bot.fetch_channel(channel_id)

                    if not isinstance(tmp_channel, discord.TextChannel):
                        #NOTE: excluding DM channels to prevent malicious use!
                        LOGGER.error("Channel is not a text channel!")
                        return

                    self.current_channel = tmp_channel
                    self.current_guild = self.current_channel.guild
                    LOGGER.info("Channel set to %s!", self.current_channel.name)
                    LOGGER.info("Server set to %s!", self.current_guild.name)
                    return

                # Get channel on the specified server
                tmp_channel = self.current_guild.get_channel(channel_id)

                if tmp_channel is None:
                    LOGGER.error("Channel not found on this server!")
                    return

                self.current_channel = tmp_channel
                LOGGER.info("Channel set to %s!", self.current_channel.name)
                return

            # Add attachment to the next msg
            if in_str_lower.startswith("file"):
                if in_str_lower == "file clear": #Clear attachment
                    self.current_attachment = None
                    LOGGER.info("Attachment removed!")
                    return

                att_url = command_str[5:]

                #Get file name from URL
                att_name = att_url.split("/")[-1].split("?")[0]

                self.current_attachment = discord.File(att_url, filename=att_name)
                LOGGER.info("Added %s as attachment!", att_url)
                return


            # Send embed
            if (in_str_lower == "send_embed"):
                if self.current_channel is None:
                    LOGGER.error("No channel selected!")
                    return

                embed_message = ""
                embed_title = ""
                embed_url = ""
                embed_description = []
                LOGGER.info("Please enter embed details:")

                try:
                    embed_message = await ainput("Mesage (optional): ")
                    embed_title = await ainput("Title: ")
                    embed_url = await ainput("Url (optional): ")

                    print("Description:")

                    while True:
                        print("> ", end="")
                        embed_description_line = await ainput("")
                        if embed_description_line == "":
                            break

                        embed_description.append(embed_description_line)

                except KeyboardInterrupt:
                    return

                await self.current_channel.send(
                    embed_message,
                    embed=discord.Embed(
                        title=embed_title,
                        url=embed_url,
                        description="\n".join(embed_description)
                    )
                )
                LOGGER.info("Embed sent to channel '%s' on '%s'!",self.current_channel.name, self.current_guild.name)
                return

            # Send message
            if in_str_lower.startswith("msg"): #Send message
                if self.current_channel is None:
                    LOGGER.error("No channel selected!")
                    return
                
                await self.current_channel.send(command_str[4:], file=self.current_attachment)
                self.current_attachment = None
                LOGGER.info("Message sent to channel '%s' on '%s'!",self.current_channel.name, self.current_guild.name)
                return

            # List things
            if in_str_lower.startswith("ls"):
                ls_res = in_str_lower[3:]

                #Auto select
                if ls_res == "":
                    if self.current_guild is None:
                        ls_res = "srv"
                    else:
                        ls_res = "ch"

                #Server
                if ls_res == "srv":
                    LOGGER.info("Current guilds: \n%s", prettylist(self.bot.guilds))
                    return

                if ls_res == "ch":
                    if self.current_guild is None:
                        LOGGER.error("No server selected!")
                        return
                    #Get Channels
                    guild_channels = self.current_guild.channels or await self.current_guild.fetch_channels()

                    LOGGER.info("Text channels on '%s': \n%s", self.current_guild.name, prettylist(
                                list(
                                    filter(
                                    lambda channel : isinstance(channel, discord.channel.TextChannel),
                                    guild_channels
                                )
                            )
                        )
                    )
                    return

                LOGGER.error("Unknown resource '%s'!", command_str[3:])
                return

            #Quit Sibelius
            if in_str_lower == "exit":
                #Confirm selection
                try:
                    return ((await ainput("Exit? [y/N]: ")).lower() == "y")
                except EOFError:
                    return True

            #Unknown command
            if command_str != "":
                LOGGER.error("Unknown command '%s'!", command_str)
                return
        except Exception as input_exception:
            LOGGER.error("Error processing user command!", exc_info=input_exception)


async def setup(bot):
    '''import and run extension'''
    await bot.add_cog(Talk(bot))