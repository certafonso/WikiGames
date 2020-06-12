import discord
import asyncio
from dotenv import load_dotenv
import os
import time
import wikipedia
import random

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
        
        await channel.send("To start The Wikipedia Game someone must type `-start` in the channel where you want the game to take place.")

    async def on_message(self, message):
        """Handles messages"""

        if message.author == client.user:
            return

        if type(message.channel) == discord.DMChannel:  # received a dm
            channel = self.user_ingame(message.author)
            if channel != None:
                await self.running_games[channel]["Game"].on_message(message)

        else:
            print(message.author.id)
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
                
                else:
                    if self.running_games[str(message.channel.id)]["WaitingPlayers"]:   # Will only work if the game didn't start
                        if message.content == "-start" and message.author == self.running_games[str(message.channel.id)]["GameMaster"]:
                            # only the gamemaster can start the game
                            await self.game_selection(message.channel)
                    else:   # message will be handled by the game
                        await self.running_games[str(message.channel.id)]["Game"].on_message(message)

    def user_ingame(self, user):
        """Checks if a user is participating in any game"""

        for channel in self.running_games.keys():
            for player in self.running_games[channel]["Players"]:
                print(user.id)
                print(player.id)
                if user.id == player.id:
                    return channel
        return None

    async def start_game(self, channel, GameMaster):
        """Starts a game in a channel"""

        if str(channel.id) in self.running_games:    #there's already a game running
            print("hey")
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
        print(self.running_games)

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
        
        print(self.running_games)

    async def display_players(self, channel):
        """Displays a list of all players"""

        if len(self.running_games[str(channel.id)]["Players"]) != 0:
            await channel.send("Player list:")
            for player in self.running_games[str(channel.id)]["Players"]:
                await channel.send(player.mention)

            # if len(self.running_games[str(channel.id)]["PlayerQueue"]) != 0:
            #     await channel.send("Players on queue:")
            #     for player in self.running_games[str(channel.id)]["PlayerQueue"]:
            #         await channel.send(player.mention)
            
            await channel.send("Type `-join` to join the game or `-leave` to leave the game.")

        else:
            await channel.send("No one is playing :(")

    async def game_selection(self, channel):
        self.running_games[str(channel.id)]["WaitingPlayers"] = False
        self.running_games[str(channel.id)]["Game"] = nPeopleAreLying(channel, self.running_games[str(channel.id)]["Players"])

        await self.running_games[str(channel.id)]["Game"].Setup_Round0()
        
    async def end_game(self, channel):
        """Ends a game"""

        self.running_games[str(channel.id)]["Game"] = None
        self.running_games[str(channel.id)]["WaitingPlayers"] = True

class nPeopleAreLying():
    def __init__(self, channel, players):
        self.Channel = channel
        self.Players = players
        self.GameStage = 0
        self.Articles = []
        self.Ready = []
        self.Guesser = None
        self.ArticleChoosen = None

    async def on_message(self, message):
        """Will handle messages for the game nPeopleAreLying"""

        command = message.content.split(" ")

        if type(message.channel) == discord.DMChannel:  # received a dm
            if self.GameStage == 0:     # game in stage 0 - aproving the articles
                if not self.Ready[self.get_index(message.author.id)]:   # the user isn't already ready
                    if command[0] == "-ready":
                        await self.AcceptArticle(self.Players[self.get_index(message.author.id)])
                    elif command[0] == "-new":
                        await self.RejectArticle(self.Players[self.get_index(message.author.id)])

        else:
            if self.GameStage == 1:     # game in stage 1 - guessing the articles
                if command[0] == "-guess" and message.author == self.Players[self.Guesser]:
                    await self.Guess(command[1])
            elif self.GameStage == 2:   # game in stage 2 - new round or quit
                if command[0] == "-play" and message.author == self.Players[0]:
                    await self.Setup_Round()

        print(self.Articles, self.Ready)

    def get_index(self, userId):
        """Returns the index of a player, given his id"""

        for i in range(0, len(self.Players)):
            if self.Players[i].id == userId:
                return i
        return None

    async def Setup_Round0(self):
        """Will setup the first round"""

        await self.Channel.send("Sending articles to everyone...")

        self.Articles = []
        for article in wikipedia.random(pages=len(self.Players)+1): # generate random articles
            try:
                self.Articles.append(wikipedia.page(article))   

            except wikipedia.exceptions.DisambiguationError as e:
                self.Articles.append(wikipedia.page(random.choice(e.options)))  # chooses a random article from the disambiguation page

            self.Ready.append(False)

        for i in range(0, len(self.Players)):
            dm = self.Players[i].dm_channel
            if dm == None:
                await self.Players[i].create_dm()
                dm = self.Players[i].dm_channel

            url = self.Articles[i].title.replace(" ", "_")
            await dm.send(f"{self.Articles[i].title}\n{self.Articles[i].summary}\nhttps://en.wikipedia.org/wiki/{url}")
            await dm.send(f"Type `-ready` once you're ready. If you want another article type `-new`.")

    async def Setup_Round(self):
        """Will setup a round"""

        self.GameStage = 0

        await self.Channel.send(f"Sending an article to {self.Players[self.ArticleChoosen].mention}...")

        article = wikipedia.random() # generate a random article

        try:
            self.Articles[self.ArticleChoosen] = wikipedia.page(article) 

        except wikipedia.exceptions.DisambiguationError as e:
            self.Articles[self.ArticleChoosen] = wikipedia.page(random.choice(e.options))  # chooses a random article from the disambiguation page

        self.Ready[self.ArticleChoosen] = False
        
        dm = self.Players[self.ArticleChoosen].dm_channel
        if dm == None:
            await self.Players[self.ArticleChoosen].create_dm()
            dm = self.Players[self.ArticleChoosen].dm_channel

        url = self.Articles[self.ArticleChoosen].title.replace(" ", "_")
        await dm.send(f"{self.Articles[self.ArticleChoosen].title}\n{self.Articles[self.ArticleChoosen].summary}\nhttps://en.wikipedia.org/wiki/{url}")
        await dm.send(f"Type `-ready` once you're ready. If you want another article type `-new`.")

    async def AcceptArticle(self, player):
        """Will add the player to the ready list once he accepted his article"""

        dm = player.dm_channel

        self.Ready[self.Players.index(player)] = True

        n_ready = self.CheckReady()

        await self.Channel.send(f"{player.mention} is ready ({n_ready}/{len(self.Ready)})")
        await dm.send(f"Great! Now wait for everyone to be ready")

        if n_ready == len(self.Players):    # everyone is ready, the game starts
            await self.StartRound()

    async def RejectArticle(self, player):
        """Will give a new article to a player"""

        dm = player.dm_channel
        i = self.Players.index(player)

        article = wikipedia.random()

        self.Articles[i] = wikipedia.page(article)

        url = self.Articles[i].title.replace(" ", "_")
        await dm.send(f"{self.Articles[i].title}\n{self.Articles[i].summary}\nhttps://en.wikipedia.org/wiki/{url}")
        await dm.send(f"Type `-ready` once you're ready. If you want another article type `-new`.")

    def CheckReady(self):
        """Counts the number of ready players"""

        n_ready = 0
        for person in self.Ready:
            if person: n_ready += 1

        return n_ready

    async def StartRound(self):
        """Selects a random player to guess and a random article"""

        self.Guesser = random.randint(0, len(self.Players)-1)
        self.ArticleChoosen = self.Guesser

        await self.Channel.send(f"{self.Players[self.Guesser].mention} is guessing.\nTo guess type `-guess` and then mention the person you think is telling the truth.")

        # while self.Guesser == self.ArticleChoosen:
        #     self.ArticleChoosen = random.randint(0, len(self.Players))

        await self.Channel.send(f"The article is {self.Articles[self.ArticleChoosen].title}.")

        self.GameStage = 1

    async def Guess(self, guess):
        """Handles a guess"""

        if guess[:3] != "<@!": # no one was mentioned
            await self.Channel.send(f"No one was mentioned\nTo guess type `-guess` and then mention the person you think is telling the truth.")
        
        else:
            if guess[3:] == self.Players[self.ArticleChoosen].mention[2:]: # guess is right
                await self.Channel.send("You're right!")
            else:                                                       # guess is wrong
                await self.Channel.send(f"You're wrong, the article was from {self.Players[self.ArticleChoosen].mention}")

            # send the article
            url = self.Articles[self.ArticleChoosen].title.replace(" ", "_")
            await self.Channel.send(f"{self.Articles[self.ArticleChoosen].title}\n{self.Articles[self.ArticleChoosen].summary}\nhttps://en.wikipedia.org/wiki/{url}")

            self.GameStage = 2

            # play again?
            await self.Channel.send(f"Type `-play` to play again or `-quit` to go to the main menu.")


if __name__ == "__main__":

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    client = Client()
    client.run(TOKEN)