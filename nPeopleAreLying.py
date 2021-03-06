import discord
import asyncio
import wikipedia
import random

class Game():
	"""Implements the game nPeopleAreLying"""
	def __init__(self, channel, players):

		self.Channel = channel
		self.Players = players
		self.GameStage = 0
		self.Articles = []
		self.Ready = []
		self.Guesser = -1
		self.ArticleChoosen = 0

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
					elif command[0] == "-submit":
						try:
							await self.ReceiveArticle(self.Players[self.get_index(message.author.id)], command[1])
						except IndexError:
							await self.Players[self.get_index(message.author.id)].dm_channel.send("You didn't write an article")

		else:
			if self.GameStage == 1:     # game in stage 1 - guessing the articles
				if command[0] == "-guess" and self.Players[self.Guesser] == message.author:
					try:
						await self.Guess(message)
					except:
						await self.Guess("")
			elif self.GameStage == 2:   # game in stage 2 - new round or quit
				if command[0] == "-play" and self.Players[0] == message.author:
					await self.Setup_Round()

	def get_index(self, userId):
		"""Returns the index of a player, given his id"""

		for i in range(0, len(self.Players)):
			if self.Players[i].id == userId:
				return i
		return None

	async def Setup_Round0(self):
		"""Will setup the first round"""

		await self.Channel.send("Sending articles to everyone...")

		self.Articles = [None] * len(self.Players)
		self.Ready = [False] * len(self.Players)

		for i in range(0, len(self.Players)): # generate random articles
			self.Articles[i] = GetArticle()
			
			dm = self.Players[i].dm_channel
			if dm == None:
				await self.Players[i].create_dm()
				dm = self.Players[i].dm_channel

			url = self.Articles[i].title.replace(" ", "_")

			try:
				await dm.send(f"""{self.Articles[i].title}\n
				{self.Articles[i].summary}\n
				https://en.wikipedia.org/wiki/{url}\n
				Type `-ready` once you're ready. If you want another article type `-new`. You can also submit your own article using `-submit [article URL]`
				""")
		
			except discord.HTTPException:	# error sending the message (probably was too long)
				await self.RejectArticle(self.Players[i])

	async def Setup_Round(self):
		"""Will setup a round"""

		self.GameStage = 0

		await self.Channel.send(f"Sending an article to {self.Players[self.ArticleChoosen].mention}...")

		self.Articles[self.ArticleChoosen] = GetArticle()

		self.Ready[self.ArticleChoosen] = False
		
		dm = self.Players[self.ArticleChoosen].dm_channel
		if dm == None:
			await self.Players[self.ArticleChoosen].create_dm()
			dm = self.Players[self.ArticleChoosen].dm_channel

		url = self.Articles[self.ArticleChoosen].title.replace(" ", "_")

		try:
			await dm.send(f"""{self.Articles[self.ArticleChoosen].title}\n
			{self.Articles[self.ArticleChoosen].summary}\n
			https://en.wikipedia.org/wiki/{url}\n
			Type `-ready` once you're ready. If you want another article type `-new`. You can also submit your own article using `-submit [article URL]`
			""")
		
		except discord.HTTPException:	# error sending the message (probably was too long)
			await self.Setup_Round()

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

		self.Articles[i] = GetArticle()

		url = self.Articles[i].title.replace(" ", "_")

		try:
			await dm.send(f"""{self.Articles[i].title}\n
			{self.Articles[i].summary}\n
			https://en.wikipedia.org/wiki/{url}\n
			Type `-ready` once you're ready. If you want another article type `-new`. You can also submit your own article using `-submit [article URL]`""")
		
		except discord.HTTPException:	# error sending the message (probably was too long)
			await self.RejectArticle(player)

	async def ReceiveArticle(self, player, url):
		"""Receives an article submited by a player"""

		try:
			dm = player.dm_channel

			title = url.split("/wiki/")[1]

			title = title.replace("_", " ")

			title = title.replace("#/random", "")	# removes #/random in case the article were randomly generated by wikipedia

			article = wikipedia.page(title)

			self.Articles[self.Players.index(player)] = article

			self.Ready[self.Players.index(player)] = True

			n_ready = self.CheckReady()

			await self.Channel.send(f"{player.mention} is ready ({n_ready}/{len(self.Ready)})")
			await dm.send(f"Great! Now wait for everyone to be ready")

			if n_ready == len(self.Players):    # everyone is ready, the game starts
				await self.StartRound()

		except wikipedia.exceptions.PageError:
			await player.dm_channel.send("An error ocurred. Please try again.")

	def CheckReady(self):
		"""Counts the number of ready players"""

		n_ready = 0
		for person in self.Ready:
			if person: n_ready += 1

		return n_ready

	async def StartRound(self):
		"""Selects a random player to guess and a random article"""
		
		new_guesser = self.Guesser

		while new_guesser == self.Guesser:		# repeating guessers is boring
			new_guesser = random.randint(0, len(self.Players)-1)

		self.Guesser = new_guesser
		self.ArticleChoosen = self.Guesser

		message = f"{self.Players[self.Guesser].mention} is guessing.\nTo guess type `-guess` and then mention the person you think is telling the truth.\n"

		while self.Guesser == self.ArticleChoosen:
			self.ArticleChoosen = random.randint(0, len(self.Players)-1)

		message += f"The article is {self.Articles[self.ArticleChoosen].title}."
		await self.Channel.send(message)

		self.GameStage = 1

	async def Guess(self, guess):
		"""Handles a guess"""

		if guess.content == guess.clean_content: # no one was mentioned
			await self.Channel.send(f"No one was mentioned\nTo guess type `-guess` and then mention the person you think is telling the truth.")
		
		else:
			if self.Players[self.ArticleChoosen].mentioned_in(guess):	# guess is right
				message = "You're right!\n"
				self.Players[self.Guesser].points += 1			# guesser gets 1 point
				self.Players[self.ArticleChoosen].points += 1	# article owner gets a point
			else:															# guess is wrong
				message = f"You're wrong, the article was from {self.Players[self.ArticleChoosen].mention}\n"
				
				for i in range(0, len(self.Players)):
				#for player in self.Players:
					if self.Players[i].mentioned_in(guess):			# finds the person o convinced the guesser
						self.Players[i].points += 1	                # gives them 1 point

			# send the article
			url = self.Articles[self.ArticleChoosen].title.replace(" ", "_")
			message += f"{self.Articles[self.ArticleChoosen].title}\n{self.Articles[self.ArticleChoosen].summary}\nhttps://en.wikipedia.org/wiki/{url}\n"

			self.GameStage = 2

			# play again?
			message += f"Type `-play` to play again or `-quit` to go to the main menu."

			await self.Channel.send(message)

	async def help(self):
		"""Displays a help menu"""

		if self.GameStage == 0:
			await self.Channel.send("Everyone will recieve a random article from wikipedia in their DMs. You can do 3 things: \n\t - Accept the article given to you by replying `-ready`;\n\t - Reject the article and ask for a new one by replying `-new`;\n\t - Submit your own article replying with `-submit` followed by the article URL.\nWhen everyone is ready, the choosen article and the guesser will appear in the discord channel and its time do play the game!")
		
		elif self.GameStage == 1:
			await self.Channel.send("When the guesser is done and wants to take a guess, you have to type `-guess` and then mention the person he thinks is telling the truth.")
		
		elif self.GameStage == 2:
			await self.Channel.send("If you want to play again the gamemaster has to type `-play`, a article new article will be sent to the replace the one that was used and the game will start again.")

def GetArticle():
	""" Generates an article """

	try:
		return wikipedia.page(wikipedia.random())

	except:  # an error ocurred, probably gone to a disambiguation page, try again
		return GetArticle()
