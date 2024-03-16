from PIL import Image, ImageDraw
from typing import Tuple, Mapping
from urllib.request import urlopen
from WeatherAPIHandler import (
    getWeatherData,
    getIconCode,
    getMinTemp,
    getMaxTemp,
    getAvgTemp,
    getDayFull,
    getDescription,
    WeatherData,
    getDayShort,
)

Color = Tuple[int, int, int]
Point = Tuple[int, int]


class Colors:
    WHITE = (255, 255, 255)
    RAISIN_BLACK = (32, 33, 36)
    DARK_CHARCOAL = (48, 49, 52)
    CAFE_NOIR = (77, 67, 29)
    SPACE_CADET = (30, 53, 89)
    JORDY_BLUE = (138, 180, 248)
    TANGERINE_YELLOW = (255, 204, 0)


class Views:
    TEMPERATURE = "Temperature"
    PRECIPITATION = "Precipitation"
    WIND = "Wind"


class WeatherImage:
    WIDTH = 700
    HEIGHT = 400
    ICON_WIDTH = 70
    CARD_WIDTH = 100
    CARD_HEIGHT = 120
    NUM_OF_CARDS = 5
    GAP = (WIDTH - (CARD_WIDTH * NUM_OF_CARDS)) // (NUM_OF_CARDS * 2)
    GRAPH_WIDTH = WIDTH - 2 * GAP
    BAR_HEIGHT_FACTOR = 10
    TEXT_HEIGHT = 10
    MIN_WIND_ICON_WIDTH = 10
    MAX_WIND_ICON_WIDTH = (WIDTH - GAP * 2) / 8

    image: Image.Image
    draw: ImageDraw.ImageDraw
    icons: Mapping[str, Image.Image] = {}
    weatherData: WeatherData
    dates: list[str]
    coords: Point
    page = 0
    view = Views.TEMPERATURE
    location: str

    def __init__(self, lat: float, lon: float, location: str) -> None:
        self.location = " ".join([word.capitalize() for word in location.split()])
        self.coords = (lat, lon)
        self.image = Image.new("RGBA", (self.WIDTH, self.HEIGHT))
        self.image.paste(Colors.RAISIN_BLACK, (0, 0, self.WIDTH - 1, self.HEIGHT - 1))
        self.draw = ImageDraw.Draw(self.image)
        self.weatherData = getWeatherData(lat, lon)
        self.dates = list(self.weatherData.keys())

    def drawRoundedRectangle(
        self, x: int, y: int, width: int, height: int, fill: Color
    ) -> None:
        self.draw.rounded_rectangle((x, y, x + width, y + height), radius=15, fill=fill)

    def clear(self) -> None:
        self.image.paste(Colors.RAISIN_BLACK, (0, 0, self.WIDTH - 1, self.HEIGHT - 1))

    def getWeatherIcon(self, iconCode: str) -> Image.Image:
        if iconCode not in self.icons:
            url = f"https://openweathermap.org/img/wn/{iconCode}@2x.png"
            self.icons[iconCode] = Image.open(urlopen(url))
        return self.icons[iconCode]

    def drawText(
        self, x: float, y: float, text: str, *, font_size=12, anchor="mt"
    ) -> None:
        self.draw.text(
            (x, y), text, anchor=anchor, fill=Colors.WHITE, font_size=font_size
        )

    def drawWeatherIcon(self, iconCode: str, x: int, y: int, size=ICON_WIDTH) -> None:
        icon = self.getWeatherIcon(iconCode).resize((size, size))
        self.image.paste(icon, (x, y, x + size, y + size), icon)

    def saveImage(self) -> str:
        fileName = f"{self.location}-{self.view}-{self.page}.png"
        self.image.save(fileName)
        return fileName

    def drawLine(self, x1: int, y1: int, x2: int, y2: int, fill: Color) -> None:
        self.draw.line([(x1, y1), (x2, y2)], fill)

    def drawQuad(self, tl: Point, tr: Point, bl: Point, br: Point, fill: Color) -> None:
        self.draw.polygon([tl, tr, bl, br], fill)

    def _drawBase(self, page: int):
        for i, date in enumerate(self.dates):
            x = self.GAP * (2 * i + 1) + (self.CARD_WIDTH * i)
            y = self.HEIGHT - self.GAP - self.CARD_HEIGHT
            bgColor = Colors.DARK_CHARCOAL if i == page else Colors.RAISIN_BLACK
            self.drawRoundedRectangle(x, y, self.CARD_WIDTH, self.CARD_HEIGHT, bgColor)
            weekday = getDayShort(date)
            self.drawText(
                x + self.CARD_WIDTH // 2, y + self.GAP // 2, weekday, font_size=20
            )
            data = self.weatherData[date]
            temp_min = getMaxTemp(data)
            temp_max = getMinTemp(data)
            self.drawText(
                x + self.CARD_WIDTH // 2,
                y + self.CARD_HEIGHT - self.GAP,
                f"{temp_min}°  {temp_max}°",
                font_size=15,
            )
            iconCode = getIconCode(data)
            x += (self.CARD_WIDTH - self.ICON_WIDTH) // 2
            y = (
                self.HEIGHT
                - self.GAP
                - self.CARD_HEIGHT
                + (self.CARD_HEIGHT - self.ICON_WIDTH) // 2
            )
            self.drawWeatherIcon(iconCode, x, y)
            data = self.weatherData[self.dates[page]]
            iconCode = getIconCode(data)
            temp = getAvgTemp(data)
            weekday = getDayFull(self.dates[page])
            description = getDescription(data)
            self.drawText(self.WIDTH / 2, self.GAP, self.location, font_size=20)
            self.drawWeatherIcon(iconCode, self.GAP, self.GAP, 90)
            self.drawText(
                self.GAP + 90 + 5, self.GAP + 30, f"{temp}°", font_size=30, anchor="lm"
            )
            self.drawText(
                self.WIDTH - self.GAP, self.GAP, weekday, font_size=25, anchor="rt"
            )
            self.drawText(
                self.WIDTH - self.GAP,
                self.GAP + 25 + 10,
                description,
                font_size=15,
                anchor="rt",
            )

    def drawChart(self, page: int, view: str) -> None:
        self.page = page
        self.view = view
        self._drawBase(page)
        self.drawText(self.WIDTH / 2, self.HEIGHT / 8, view, font_size=15)
        if view == Views.TEMPERATURE:
            self.drawTemperatureGraph()
        elif view == Views.PRECIPITATION:
            self.drawPrecipitationGraph()
        elif view == Views.WIND:
            self.drawWindGraph()

    def drawPrecipitationGraph(self) -> None:
        data = self.weatherData[self.dates[self.page]]
        times = [d["time"] for d in data]
        rains = [d["rain"] for d in data]
        y2 = self.HEIGHT - self.GAP * 2 - self.CARD_HEIGHT
        width = (self.WIDTH - self.GAP * 2) / len(data)
        for i in range(len(data)):
            x1 = self.GAP + width * i
            x2 = self.GAP + width * (i + 1)
            y1 = y2 - rains[i] * self.BAR_HEIGHT_FACTOR * 2
            self.drawQuad((x1, y1), (x2, y1), (x2, y2), (x1, y2), Colors.SPACE_CADET)
            self.drawLine(x1, y1, x2, y1, Colors.JORDY_BLUE)
            self.drawText(x1 + width / 2, y2 + 5, times[i])
            self.drawText(x1 + width / 2, y1 - 5, f"{rains[i]} mm", anchor="mb")

    def drawArrow(self, x: int, y: int, width: int, angle: float) -> None:
        with Image.open("wind_icon.png") as icon:
            resizedIcon = icon.resize((width, width)).rotate(angle)
            self.image.paste(resizedIcon, (x, y), resizedIcon)

    def drawWindGraph(self) -> None:
        max_width = (self.WIDTH - 2 * self.GAP) / 8
        max_height = self.HEIGHT - self.GAP * 3 - self.CARD_HEIGHT - 90
        data = self.weatherData[self.dates[self.page]]
        speeds = [d["wind_speed"] * 3.6 for d in data]
        degs = [d["wind_deg"] for d in data]
        times = [d["time"] for d in data]
        left = self.WIDTH / 2 - max_width / 2 * len(data)
        y = self.GAP + 90

        for i in range(len(data)):
            width = max(
                self.MIN_WIND_ICON_WIDTH, min(self.MAX_WIND_ICON_WIDTH, speeds[i] * 1.5)
            )
            x_offset = (max_width - width) / 2
            y_offset = (max_height - width) / 2
            x = left + max_width * i
            self.drawText(
                int(x + max_width / 2),
                int(y),
                f"{round(speeds[i])} km/h",
                anchor="mb",
                font_size=15,
            )
            self.drawArrow(int(x + x_offset), int(y + y_offset), int(width), degs[i])
            self.drawText(x + max_width / 2, y + max_height, times[i])

    def drawTemperatureGraph(self) -> None:
        data = self.weatherData[self.dates[self.page]]
        times = [d["time"] for d in data]
        temps = [d["temp"] for d in data]
        minTemp = min(temps) - 1
        width = self.GRAPH_WIDTH / len(temps)
        y = self.HEIGHT - self.GAP * 2 - self.CARD_HEIGHT - self.TEXT_HEIGHT
        temps = [temps[0]] + temps
        times = [times[0]] + times
        for j in range(len(temps) - 1):
            x1 = self.GAP + width * j
            x2 = self.GAP + width * (j + 1)
            y1 = y - (temps[j] - minTemp) * self.BAR_HEIGHT_FACTOR
            y2 = y - (temps[j + 1] - minTemp) * self.BAR_HEIGHT_FACTOR
            self.drawQuad((x1, y1), (x2, y2), (x2, y), (x1, y), Colors.CAFE_NOIR)
            self.drawLine(x1, y1, x2, y2, Colors.TANGERINE_YELLOW)
            textX = x1 + width / 2
            self.drawText(
                textX, min(y1, y2) - 5, f"{round(temps[j + 1], 1)}°", anchor="mb"
            )
            self.drawText(textX, y + self.TEXT_HEIGHT, times[j + 1])
