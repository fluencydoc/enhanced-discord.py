# This example requires the 'members' privileged intents

import discord


class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

    async def on_member_join(self, member):
        """
        When a member joins the server, send them a message welcoming them to the
        server.
        """
        guild = member.guild
        if guild.system_channel is not None:
            to_send = f"Welcome {member.mention} to {guild.name}!"
            await guild.system_channel.send(to_send)


client = MyClient(intents=discord.Intents(guilds=True, members=True))
client.run("token")
