import discord
import asyncio
import wikipedia
import re

class Game():
	"""Implements the game WikiAgainstHumanity"""
	def __init__(self, channel, players):

		self.Channel = channel
		self.Players = players
		self.GameStage = 0
		self.Answers = []
		self.submissions = []
		self.article = ""
		self.article_text = ""

	async def on_message(self, message):
		"""Will handle messages for the game WikiAgainstHumanity"""

		command = message.content.split(" ")

		if type(message.channel) == discord.DMChannel:  # received a dm
			if self.GameStage == 0:		# game in stage 0, receiving submissions
				if command[0] == "-submit":
					await self.Receive_Submit(message.author, " ".join(command[1:]))

		# else:
		# 	if self.GameStage == 1:     # game in stage 1 - guessing the articles
		# 		if command[0] == "-guess" and message.author == self.Players[self.Guesser]:
		# 			await self.Guess(command[1])
		# 	elif self.GameStage == 2:   # game in stage 2 - new round or quit
		# 		if command[0] == "-play" and message.author == self.Players[0]:
		# 			await self.setup()

	async def setup(self):
		"""Starts the round"""

		self.GameStage = 0

		self.Get_Article()	# selects an article

		await self.Channel.send("Sending article to everyone...")

		for i in range(0, len(self.Players)):	# sends the message to everyone
			dm = self.Players[i].dm_channel
			if dm == None:
				await self.Players[i].create_dm()
				dm = self.Players[i].dm_channel

			await dm.send(f"""{self.article_text}\n
			Type `-submit` followed by the text you want to submit
			""")

			try:
				self.submissions[i] = ""
			except IndexError:
				self.submissions.append("")

	def Get_Article(self):
		""" Gets a new article and removes the title """

		# chooses an article
		try:
			self.article = wikipedia.page(wikipedia.random())

		except wikipedia.exceptions.DisambiguationError:

			self.article = wikipedia.page(wikipedia.random())	# generates new article

		except wikipedia.exceptions.PageError:  # something weird happened let's just try again
			self.Get_Article()
			return

		# removes the article title

		pattern = re.compile(re.escape(self.article.title), re.IGNORECASE)
		
		if len(re.findall(pattern, self.article.summary)) != 0:	# the name of the article must appear on the summary for it to work
			self.article_text = pattern.sub("___________", self.article.summary)
		
		else:
			self.Get_Article()
			return

		# if len(self.article_text.split("\n")) > 1:
		# 	self.setup()
		# 	return

		# print(self.article.title)
		# print(self.article_text)

	async def Receive_Submit(self, player, submission):
		"""Registers a submission"""

		dm = player.dm_channel

		self.submissions[self.Players.index(player)] = submission

		n_ready = self.CheckReady()

		await self.Channel.send(f"{player.mention} is ready ({n_ready}/{len(self.submissions)})")
		await dm.send(f"Great! Now wait for everyone to be ready")

		print(self.submissions)

		# if n_ready == len(self.Players):    # everyone is ready, the game starts
		# 	await self.StartRound()

	def CheckReady(self):
		"""Counts the number of ready players"""

		n_ready = 0
		for person in self.submissions:
			if person != "":
				n_ready += 1

		return n_ready

