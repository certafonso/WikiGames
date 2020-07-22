import discord
import asyncio
import wikipedia
import random
import re

class Game():
	"""Implements the game WikiAgainstHumanity"""
	def __init__(self, channel, players):

		self.Channel = channel
		self.Players = players
		self.GameStage = 0
		self.Ready = []
		self.submissions = []
		self.VotingOrder = []
		self.Votes = []
		self.article = ""
		self.article_text = ""

	async def on_message(self, message):
		"""Will handle messages for the game WikiAgainstHumanity"""

		command = message.content.split(" ")

		if type(message.channel) == discord.DMChannel:  # received a dm
			if self.GameStage == 0:		# game in stage 0, receiving submissions
				if command[0] == "-submit":
					await self.Receive_Submit(message.author, " ".join(command[1:]))

			elif self.GameStage == 1:	# game in stage 1, receiving votes
				if command[0] == "-vote":
					try:
						await self.Receive_Vote(message.author, command[1])
					except IndexError:
						await self.Receive_Vote(message.author, None)

		else:
			if self.GameStage == 1:	# game in stage 1, receiving votes
				if command[0] == "-vote":
					await self.Channel.send("To vote you have to dm the bot `-vote [option]`")

			elif self.GameStage == 2:   # game in stage 2 - new round or quit
				if command[0] == "-play" and message.author == self.Players[0]:
					await self.setup()

	async def setup(self):
		"""Starts the round"""

		self.GameStage = 0
		self.Ready = [False for j in range(0, len(self.Players))]		# resets ready
		self.submissions = ["" for j in range(0, len(self.Players))]	# resets submissions
		self.Get_Article()	# selects an article

		await self.Channel.send("Sending the article to everyone...")

		for i in range(0, len(self.Players)):	# sends the message to everyone
			dm = self.Players[i].dm_channel
			if dm == None:
				await self.Players[i].create_dm()
				dm = self.Players[i].dm_channel

			try:
				await dm.send(f"""{self.article_text}\n
				Type `-submit` followed by the text you want to submit
				""")
			except discord.errors.HTTPException:	# probably the article was too long, let's try again
				await self.Channel.send("An error ocurred, sending another article...")

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

		if self.Ready[self.Players.index(player)]:	# can't submit twice
			await dm.send("You already made a submission")
		elif submission == "":						# submission can't be empty
			await dm.send("You didn't put any text")
		else:
			self.submissions[self.Players.index(player)] = submission
			self.Ready[self.Players.index(player)] = True

			n_ready = self.CheckReady()

			await self.Channel.send(f"{player.mention} is ready ({n_ready}/{len(self.submissions)})")
			await dm.send(f"Great! Now wait for everyone to be ready")

			print(self.submissions)

			if n_ready == len(self.Ready):	# everyone is ready, voting time!
				await self.Start_Voting()

	def CheckReady(self):
		"""Counts the number of ready players"""

		n_ready = 0
		for person in self.Ready:
			if person: n_ready += 1

		return n_ready

	async def Start_Voting(self):
		"""Displays all the submissions and opens voting"""

		# Display the submissions

		cnt = 0

		message = self.article_text + "\n"

		order = list(range(0, len(self.submissions)))
		random.shuffle(order)	#shuffle the articles

		self.VotingOrder = [0 for j in range(0, len(self.submissions))]	# resets voting order

		for i in order:	# display the articles
			message += f"\n{cnt} - {self.submissions[i]}"
			self.VotingOrder[i] = cnt
			cnt += 1

		message += "\n\nTo vote dm me `-vote [option]`. Obviously you can't vote for yourself."

		self.Votes = [0 for j in range(0, len(self.submissions))]	# resets votes
		self.Ready = [False for j in range(0, len(self.Ready))]		# resets ready

		await self.Channel.send(message)

		self.GameStage = 1
		
	async def Receive_Vote(self, player, vote):
		"""Receives a vote"""

		dm = player.dm_channel

		if self.Ready[self.Players.index(player)]:	# can't vote twice
			await dm.send("You can't vote twice")
		else:
			if vote == None:	#didn't put an optin
				await dm.send("You didn't specify an option. To vote dm me `-vote [option]`.")
				return

			try:
				vote = int(vote)
			except:
				await dm.send("An error ocurred! Check if you inserted a number.")
				return

			if vote >= len(self.Players) or vote < 0:	#checks if vote is valid
				await dm.send("Invalid Vote.")
				return

			real_vote = self.VotingOrder[vote]

			if real_vote != self.Players.index(player):	# player voted on another person
				self.Votes[real_vote] += 1			
				self.Ready[self.Players.index(player)] = True

				n_ready = self.CheckReady()

				await self.Channel.send(f"{player.mention} voted ({n_ready}/{len(self.Ready)})")
				await dm.send(f"Great! Now wait for everyone to be ready")

				n_ready = self.CheckReady()

				if n_ready == len(self.Players):	# everyone voted
					await self.Count_Votes()

			else:
				await dm.send("You can't vote in yourself")

	async def Count_Votes(self):
		""" Counts the votes and displays the result """

		self.GameStage = 2

		message = "And the results are... \n"

		for i in range(0, len(self.Players)):
			message += f"\"{self.submissions[i]}\" {self.Players[i].mention} - {self.Votes[i]} votes \n"

		message += f"The winner is {self.Players[self.Votes.index(max(self.Votes))].mention} \n"

		# play again?
		message += f"Type `-play` to play again or `-quit` to go to the main menu."

		await self.Channel.send(message)

	async def help(self):
		"""Displays a help menu"""

		if self.GameStage == 0:
			await self.Channel.send("Everyone will receive the same article with the title redacted, you have to submit a new funny title to the article, by replying `-submit [your title]` to the bot. \nOnce everyone is ready, all submissions will be displayed and it's time to vote on the best one!")
		
		elif self.GameStage == 1:
			await self.Channel.send("To vote you have to dm the bot `-vote [option]`. You can't vote in yourself.")
		
		elif self.GameStage == 2:
			await self.Channel.send("If you want to play again the gamemaster has to type `-play` and the game will restart.")
