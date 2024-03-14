import discord
import WeatherImageGenerator as WI
from WeatherAPIHandler import getLatLon
import time
from typing import Mapping, TypedDict
from Constants import BOT_TOKEN


class State(TypedDict):
    current: int
    location: str
    lat: float
    lon: float
    view: int
    time: str


States = Mapping[int, State]

MAX_TIME_ALLOWED = 60

class MyClient(discord.Client):
    ONE_SECOND = 1
    FORWARD_EMOJI = "➡"
    BACKWARD_EMOJI = "⬅"
    CROSS_EMOJI = "❌"
    TEMPERATURE_EMOJI = "🌡️"
    RAIN_EMOJI = "🌧️"
    WIND_EMOJI = "💨"
    EMOJIS = (
        TEMPERATURE_EMOJI,
        RAIN_EMOJI,
        WIND_EMOJI,
        BACKWARD_EMOJI,
        FORWARD_EMOJI,
        CROSS_EMOJI,
    )
    
    states: States = {}
    
    def gen_attachment(self, current: int, view: int, lat: float, lon: float, location: str):
        wi = WI.WeatherImage(lat, lon, location)
        wi.drawChart(current, view)
        filename = wi.saveImage()
        file = discord.File(filename)
        embed = discord.Embed()
        embed.set_image(url=f"attachment://{filename}")
        return file, embed

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content.startswith("/weather"):
            return
        channel = message.channel
        await message.delete(delay=self.ONE_SECOND)
        location = message.content[8:].strip()
        if not location:
            return await channel.send(
                "No location provided", delete_after=self.ONE_SECOND * 3
            )
        outcome = getLatLon(location)
        if not outcome:
            return await channel.send(outcome.error, delete_after=self.ONE_SECOND * 3)
        lat, lon = outcome.result
        current = 0
        file, embed = self.gen_attachment(current, WI.Views.TEMPERATURE, lat, lon, location)
        imageMessage = await channel.send(file=file, embed=embed)
        key = (channel.id, imageMessage.id)
        self.states[key] = {
            "current": current,
            "location": location,
            "lat": lat,
            "lon": lon,
            "view": WI.Views.TEMPERATURE,
            "time": time.time(),
        }

        for emoji in self.EMOJIS:
            await imageMessage.add_reaction(emoji)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        channel_id = reaction.message.channel.id
        message_id = reaction.message.id
        key = (channel_id, message_id)
        if key in self.states:
            emoji = str(reaction)
            if emoji in self.EMOJIS:
                state = self.states[key]
                current, location, lat, lon, view, t = state.values()
                time_ellapsed = time.time() - t
                if time_ellapsed >= MAX_TIME_ALLOWED:
                    del self.states[key]
                elif emoji == self.FORWARD_EMOJI and current < 4:
                    current += 1
                elif emoji == self.BACKWARD_EMOJI and current > 0:
                    current -= 1
                elif emoji == self.CROSS_EMOJI:
                    channel = self.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    await message.delete()
                    del self.states[key]
                elif emoji == self.RAIN_EMOJI:
                    view = WI.Views.PRECIPITATION
                elif emoji == self.WIND_EMOJI:
                    view = WI.Views.WIND
                elif emoji == self.TEMPERATURE_EMOJI:
                    view = WI.Views.TEMPERATURE
                if state["current"] != current or state["view"] != view:
                    state["current"] = current
                    state["view"] = view
                    state["time"] = time.time()
                    file, embed = self.gen_attachment(current, view, lat, lon, location)
                    channel = self.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed, attachments=[file])
                await message.remove_reaction(reaction, user)


intents = discord.Intents.default()
intents.message_content = True


client = MyClient(intents=intents)
client.run(BOT_TOKEN)
