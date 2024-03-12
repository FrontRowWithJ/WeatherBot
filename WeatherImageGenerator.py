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
    SHARK_BLACK = (32, 33, 36)
    EBONY = (48, 49, 52)
    DARK_ORANGE = (77, 67, 29)


class Views:
    TEMPERATURE: int = 0
    PRECIPITATION: int = 1
    WIND: int = 2


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
    LABELS = ["Temperature", "Precipitation", "Wind"]

    image: Image.Image
    draw: ImageDraw.ImageDraw
    icons: Mapping[str, Image.Image] = {}
    weatherData: WeatherData
    dates: list[str]
    coords: Point
    current = 0
    view = Views.TEMPERATURE
    location: str

    def __init__(self, lat: float, lon: float, location: str) -> None:
        self.location = location.capitalize()
        self.coords = (lat, lon)
        self.image = Image.new("RGBA", (self.WIDTH, self.HEIGHT))
        self.image.paste(Colors.SHARK_BLACK, (0, 0, self.WIDTH - 1, self.HEIGHT - 1))
        self.draw = ImageDraw.Draw(self.image)
        self.weatherData = getWeatherData(lat, lon)
        self.dates = list(self.weatherData.keys())

    def drawRoundedRectangle(
        self, x: int, y: int, width: int, height: int, fill: Color
    ) -> None:
        self.draw.rounded_rectangle((x, y, x + width, y + height), radius=15, fill=fill)

    def clear(self) -> None:
        self.image.paste(Colors.SHARK_BLACK, (0, 0, self.WIDTH - 1, self.HEIGHT - 1))

    def getWeatherIcon(self, iconCode: str) -> Image.Image:
        if iconCode not in self.icons:
            url = f"https://openweathermap.org/img/wn/{iconCode}@2x.png"
            self.icons[iconCode] = Image.open(urlopen(url))
        return self.icons[iconCode]

    def drawText(self, x: int, y: int, text: str, *, font_size=20, anchor="mt") -> None:
        self.draw.text(
            (x, y), text, anchor=anchor, fill=Colors.WHITE, font_size=font_size
        )

    def drawWeatherIcon(self, iconCode: str, x: int, y: int, size=ICON_WIDTH) -> None:
        icon = self.getWeatherIcon(iconCode).resize((size, size))
        self.image.paste(icon, (x, y, x + size, y + size), mask=icon)

    def saveImage(self) -> str:
        fileName = f"{self.location}-{self.LABELS[self.view]}-{self.current}.png"
        self.image.save(fileName)
        return fileName

    def drawLine(self, x1: int, y1: int, x2: int, y2: int, fill: Color) -> None:
        self.draw.line([(x1, y1), (x2, y2)], fill)

    def drawQuad(self, tl: Point, tr: Point, bl: Point, br: Point, fill: Color) -> None:
        self.draw.polygon([tl, tr, bl, br], fill)
        self.draw.line([tl, tr], (255, 204, 0))

    def drawBase(self, current: int):
        self.current = current
        for i, date in enumerate(self.dates):
            x = self.GAP * (2 * i + 1) + (self.CARD_WIDTH * i)
            y = self.HEIGHT - self.GAP - self.CARD_HEIGHT
            bgColor = Colors.EBONY if i == current else Colors.SHARK_BLACK
            self.drawRoundedRectangle(x, y, self.CARD_WIDTH, self.CARD_HEIGHT, bgColor)
            weekday = getDayShort(date)
            self.drawText(x + self.CARD_WIDTH // 2, y + self.GAP // 2, weekday)
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

    def drawCurrent(self, current: int, view: int) -> None:
        self.current = current
        label = self.LABELS[view]
        data = self.weatherData[self.dates[current]]
        iconCode = getIconCode(data)
        temp = getAvgTemp(data)
        weekday = getDayFull(self.dates[current])
        description = getDescription(data)
        self.drawText(
            self.WIDTH / 2, self.GAP, self.location, anchor="mt", font_size=20
        )
        self.drawText(self.WIDTH / 2, self.HEIGHT / 8, label, anchor="mt", font_size=15)
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
        if view == Views.TEMPERATURE:
            self.drawTemperatureGraph()
        elif view == Views.PRECIPITATION:
            self.drawPrecipitationGraph()
        elif view == Views.WIND:
            self.drawWindGraph()

    def drawPrecipitationGraph(self) -> None:
        pass

    def drawWindGraph(self) -> None:
        pass

    def drawTemperatureGraph(self) -> None:
        data = self.weatherData[self.dates[self.current]]
        times = [d["time"] for d in data]
        temps = [d["temp"] for d in data]
        width = self.GRAPH_WIDTH / len(temps)
        y = self.HEIGHT - self.GAP * 2 - self.CARD_HEIGHT
        x1 = self.GAP
        x2 = self.GAP + width
        y1 = y - temps[0] * self.BAR_HEIGHT_FACTOR
        y2 = y
        textY = y - temps[0] * self.BAR_HEIGHT_FACTOR
        self.drawQuad(
            (x1, y1),
            (x2, y1),
            (x2, y2 - self.TEXT_HEIGHT),
            (x1, y2 - self.TEXT_HEIGHT),
            Colors.DARK_ORANGE,
        )
        j = 0
        while j < len(temps) - 1:
            x1 = self.GAP + width * (j + 1)
            x2 = self.GAP + width * (j + 2)
            y1 = y - temps[j] * self.BAR_HEIGHT_FACTOR
            y2 = y - temps[j + 1] * self.BAR_HEIGHT_FACTOR
            self.drawQuad(
                (x1, y1),
                (x2, y2),
                (x2, y - self.TEXT_HEIGHT),
                (x1, y - self.TEXT_HEIGHT),
                Colors.DARK_ORANGE,
            )
            a = y - temps[j] * self.BAR_HEIGHT_FACTOR
            b = y - temps[j + 1] * self.BAR_HEIGHT_FACTOR
            textX = x1 + width / 2
            textY = min(a, b)
            self.drawText(
                textX,
                textY - 5,
                str(round(temps[j + 1], 1)),
                font_size=12,
                anchor="mb",
            )
            self.drawText(x1 + width / 2, y, times[j + 1], font_size=12)
            j += 1
        self.drawText(
            self.GAP + width / 2,
            y - temps[0] * self.BAR_HEIGHT_FACTOR - 5,
            str(round(temps[0], 1)),
            font_size=12,
            anchor="mb",
        )
        self.drawText(self.GAP + width / 2, y, times[0], font_size=12)
