import discord
import asyncio
from dotenv import load_dotenv
import os
import time
import wikipedia
import random
import nPeopleAreLying
import WikiAgainstHumanity

class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.running_games = {}

        # self.bg_task = self.loop.create_task(self.check_clock())

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_guild_join(self, guild):
        print("Entered")
        print(guild.name)
        
        channel = guild.system_channel
        
        await channel.send("To start The Wikipedia Game someone must type `-wikigames` in the channel where you want the game to take place.")

    async def on_message(self, message):
        """Handles messages"""

        if message.author == client.user:
            return

        if type(message.channel) == discord.DMChannel:  # received a dm
            channel = self.user_ingame(message.author)
            if channel != None:
                await self.running_games[channel]["Game"].on_message(message)

        else:
            if message.content == "-wikigames":             # command to start a game
                await self.start_game(message.channel, message.author)           
            elif str(message.channel.id) in self.running_games:  # there's a game running in the channel
                # Commands that will always work 
                if message.content == "-join":          
                    await self.join_player(message.channel, message.author)
                elif message.content == "-leave":
                    await self.leave_player(message.channel, message.author)
                elif message.content == "-list":      
                    await self.display_players(message.channel)
                elif message.content == "-quit":
                    await self.end_game(message.channel)
                elif message.content == "-help":
                    await self.help(message.channel)
                
                else:
                    if self.running_games[str(message.channel.id)]["WaitingPlayers"]:   # Will only work if the game didn't start
                        if message.content.split(" ")[0] == "-play" and message.author == self.running_games[str(message.channel.id)]["GameMaster"]:
                            # only the gamemaster can start the game
                            await self.game_selection(message.channel, message.content.split(" "))
                    else:   # message will be handled by the game
                        await self.running_games[str(message.channel.id)]["Game"].on_message(message)

    def user_ingame(self, user):
        """Checks if a user is participating in any game"""

        for channel in self.running_games.keys():
            for player in self.running_games[channel]["Players"]:
                # print(user.id)
                # print(player.id)
                if user.id == player.id:
                    return channel
        return None

    async def start_game(self, channel, GameMaster):
        """Starts a game in a channel"""

        if str(channel.id) in self.running_games:    #there's already a game running
            await channel.send("There is already a game running in this channel.")
        else:
            self.running_games.update(
                {str(channel.id): {
                    "GameMaster" : GameMaster,
                    "WaitingPlayers" : True,
                    "Players" : [GameMaster],
                    # "PlayerQueue" : [],
                    "Game" : None
                }
            })
            await channel.send("Welcome to the Wikipedia Game. To join the game type `-join`.")

    async def join_player(self, channel, player):
        """Adds a player to a game"""

        if player in self.running_games[str(channel.id)]["Players"]:    # player already in the game
            await channel.send(f"You're already in the game.")

        # elif player in self.running_games[str(channel.id)]["PlayerQueue"]:  # player already in the queue
        #     await channel.send(f"You're already in the queue, you'll start playing when this round ends.")

        elif self.running_games[str(channel.id)]["WaitingPlayers"]:   # the game didn't start, add to the player list
            await channel.send(f"Welcome to the Wikipedia Game {player.mention}.")
            self.running_games[str(channel.id)]["Players"].append(player)
            await self.display_players(channel)

    async def leave_player(self, channel, player):
        """Removes a player from a game"""

        if self.running_games[str(channel.id)]["GameMaster"] == player: # the player is the gamemaster so the game ends
            await channel.send(f"The game will now end because the GameMaster hates fun.")
            self.running_games.pop(str(channel.id))

        else:
            if player in self.running_games[str(channel.id)]["Players"]:
                self.running_games[str(channel.id)]["Players"].remove(player)
            # elif player in self.running_games[str(channel.id)]["PlayerQueue"]:
            #     self.running_games[str(channel.id)]["PlayerQueue"].remove(player)
            await channel.send(f"Bye {player.mention}")
        
        # print(self.running_games)

    async def display_players(self, channel):
        """Displays a list of all players"""

        message = ""

        if len(self.running_games[str(channel.id)]["Players"]) != 0:
            message += "Player list:\n"
            for player in self.running_games[str(channel.id)]["Players"]:
                message += player.mention + "\n"

            # if len(self.running_games[str(channel.id)]["PlayerQueue"]) != 0:
            #     await channel.send("Players on queue:")
            #     for player in self.running_games[str(channel.id)]["PlayerQueue"]:
            #         await channel.send(player.mention)
            
            message += "Type `-join` to join the game or `-leave` to leave the game."

        else:
            message += "No one is playing :("

        await channel.send(message)

    async def game_selection(self, channel, command):

        if len(command) == 1:   # didn't specify a game
            await channel.send("Which game do you want to play? \nGames available: nPeopleAreLying and WikiAgainstHumanity \nType `-play [game name]`")

        elif len(command) == 2: # a game was specified
            player_count = len(self.running_games[str(channel.id)]["Players"])

            if command[1] == "nPeopleAreLying":   
                if player_count >= 2:       # you need 3 people to play nPeopleAreLying
                    self.running_games[str(channel.id)]["WaitingPlayers"] = False
                    self.running_games[str(channel.id)]["Game"] = nPeopleAreLying.Game(channel, self.running_games[str(channel.id)]["Players"])

                    await self.running_games[str(channel.id)]["Game"].Setup_Round0()
                else:
                    await channel.send(f"You need at least 3 players to play nPeopleAreLying, you have {player_count}.")
                    return
            
            elif command[1] == "WikiAgainstHumanity":
                if player_count >= 2:       # you need 3 people to play WikiAgainstHumanity
                    self.running_games[str(channel.id)]["WaitingPlayers"] = False
                    self.running_games[str(channel.id)]["Game"] = WikiAgainstHumanity.Game(channel, self.running_games[str(channel.id)]["Players"])

                    await self.running_games[str(channel.id)]["Game"].setup()
                else:
                    await channel.send(f"You need at least 3 players to play WikiAgainstHumanity, you have {player_count}.")
                    return

            else:
                await channel.send("Invalid Game. \nGames available: nPeopleAreLying and WikiAgainstHumanity \nType `-play [game name]`")

        else:
            await channel.send("Invalid Command. \nType `-play [game name]`")
        
    async def end_game(self, channel):
        """Ends a game"""

        self.running_games[str(channel.id)]["Game"] = None
        self.running_games[str(channel.id)]["WaitingPlayers"] = True

        await channel.send("GoodBye")

    async def help(self, channel):
        """Displays a help menu"""

        if str(channel.id) not in self.running_games:               # not in game
            await channel.send("To start a game you have to type `-wikigames` in the channel you want to use, the person who does this will be the gamemaster and will control various aspects of the game, then everyone who wants to play has to type `-join`.")
        
        elif self.running_games[str(channel.id)]["WaitingPlayers"]: # waiting players
            await channel.send("Everyone that wants to play has to type `-join`.\nCurrently there is only one game: nPeopleAreLying (minimum of 3 players). To play it, the gamemaster needs to type `-start` in chat.")
        
        else:                                                       # in game
            await self.running_games[str(channel.id)]["Game"].help()

if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    client = Client()
    client.run(TOKEN)