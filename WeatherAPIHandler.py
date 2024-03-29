from typing import List, Mapping, TypedDict
import requests
import datetime
from Outcome import Outcome
from Constants import WEATHER_API_KEY

LIMIT = 1


class Item(TypedDict):
    dt: int
    temp: float
    main: str
    description: float
    rain: float
    time: str
    icon: str
    wind_speed: float
    wind_deg: float


WeatherData = Mapping[str, List[Item]]


def getLatLon(location: str) -> Outcome[tuple[float, float]]:
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit={LIMIT}&appid={WEATHER_API_KEY}"
    json = requests.get(url).json()
    if not json:
        return Outcome(
            error="Invalid location given", errorType=Outcome.INVALID_LOCATION
        )
    return Outcome((json[0]["lat"], json[0]["lon"]))


def getWeatherData(lat: float, lon: float) -> WeatherData:
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={WEATHER_API_KEY}"
    json = requests.get(url).json()
    group: WeatherData = {}
    for blob in json["list"]:
        date, time = blob["dt_txt"].split()
        item = {
            "dt": blob["dt"],
            "temp": blob["main"]["temp"],
            "temp_min": blob["main"]["temp_min"],
            "temp_max": blob["main"]["temp_max"],
            "main": blob["weather"][0]["main"],
            "description": blob["weather"][0]["description"],
            "rain": blob.get("rain", {"": 0}).get("3h", 0),
            "time": time[0:-3],
            "icon": blob["weather"][0]["icon"],
            "wind_speed": blob["wind"]["speed"],
            "wind_deg": blob["wind"]["deg"],
        }
        if date in group:
            group[date].append(item)
        else:
            group[date] = [item]
    return group


def getIconCode(data: List[Item]) -> str:
    icons = [d["icon"] for d in data]
    return max(icons, key=icons.count)


def getDescription(data: List[Item]) -> str:
    descriptions = [d["description"] for d in data]
    return max(descriptions, key=descriptions.count)


def getMinTemp(data: List[Item]) -> float:
    return round(min([d["temp_min"] for d in data]), 1)


def getMaxTemp(data: List[Item]) -> float:
    return round(max([d["temp_max"] for d in data]), 1)


def getAvgTemp(data: List[Item]) -> int:
    temps = [d["temp"] for d in data]
    return round(sum(temps) / len(temps), 1)


def getDayFull(dateStr: str) -> str:
    date = datetime.datetime.strptime(dateStr, "%Y-%m-%d")
    return date.strftime("%A")


def getDayShort(dateStr: str) -> str:
    date = datetime.datetime.strptime(dateStr, "%Y-%m-%d")
    return date.strftime("%a")
