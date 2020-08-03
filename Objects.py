import discord

class Player():
	def __init__(self, discord_Member):
		self.points = 0
		self.Member = discord_Member

	def __eq__(self, other):
		if type(other) == discord.Member:
			return self.Member == other

		else:
			return self == other

	def __getattr__(self, attr):
		# Trying to get something from the Member
		return getattr(self.Member, attr)