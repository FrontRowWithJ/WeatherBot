import discord
import WeatherImageGenerator as WI
from WeatherAPIHandler import getLatLon
import time
from typing import TypedDict, Protocol, Optional
from Constants import BOT_TOKEN


class State(TypedDict):
    page: int
    view: str
    location: str
    lat: float
    lon: float
    time: int


class _EmbedFieldProxy(Protocol):
    name: Optional[str]
    value: Optional[str]
    inline: bool


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

    CASTERS = {
        "page": int,
        "location": str,
        "lat": float,
        "lon": float,
        "view": str,
        "time": int,
    }

    def gen_attachment(self, state: State):
        wi = WI.WeatherImage(state["lat"], state["lon"], state["location"])
        wi.drawChart(state["page"], state["view"])
        filename = wi.saveImage()
        file = discord.File(filename)
        embed = discord.Embed()
        for key in state:
            embed.add_field(name=key, value=state[key])
        embed.set_image(url=f"attachment://{filename}")
        return file, embed

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content.startswith("/weather"):
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
        page = 0
        state: State = {
            "page": page,
            "view": WI.Views.TEMPERATURE,
            "location": location,
            "lat": lat,
            "lon": lon,
            "time": int(time.time()),
        }
        file, embed = self.gen_attachment(state)
        imageMessage = await channel.send(file=file, embed=embed)
        for emoji in self.EMOJIS:
            await imageMessage.add_reaction(emoji)

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return
        emoji = str(reaction)
        if emoji in self.EMOJIS:
            channel_id = reaction.message.channel.id
            message_id = reaction.message.id
            channel = self.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            currState = self.getState(message.embeds[0].fields)
            page, view, t = currState["page"], currState["view"], currState["time"]
            time_ellapsed = time.time() - t
            if time_ellapsed < MAX_TIME_ALLOWED:
                if emoji == self.FORWARD_EMOJI and page < 4:
                    page += 1
                elif emoji == self.BACKWARD_EMOJI and page > 0:
                    page -= 1
                elif emoji == self.CROSS_EMOJI:
                    await message.delete()
                elif emoji == self.RAIN_EMOJI:
                    view = WI.Views.PRECIPITATION
                elif emoji == self.WIND_EMOJI:
                    view = WI.Views.WIND
                elif emoji == self.TEMPERATURE_EMOJI:
                    view = WI.Views.TEMPERATURE
                if currState["view"] != view or currState["page"] != page:
                    currState["view"] = view
                    currState["page"] = page
                    currState["time"] = int(time.time())
                    file, embed = self.gen_attachment(currState)
                    await message.edit(embed=embed, attachments=[file])
            await message.remove_reaction(reaction, user)

    def getState(self, fields: list[_EmbedFieldProxy]):
        state: State = {}
        for field in fields:
            state[field.name] = self.CASTERS[field.name](field.value)
        return state


intents = discord.Intents.default()
intents.message_content = True


client = MyClient(intents=intents)
client.run(BOT_TOKEN)
