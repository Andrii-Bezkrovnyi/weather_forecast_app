import os
import pprint

import requests
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()


WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "YOUR_API_KEY")

BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
CITIES = ["Chisinau", "Madrid", "Kyiv", "Amsterdam"]


def get_next_day_forecast(city: str, api_key: str):
    # days=2, because we want the forecast for the next day, and the API returns today + next day
    params = {
        "key": api_key,
        "q": city,
        "days": 2,
        "aqi": "no",
        "alerts": "no"
    }

    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    # pprint.pprint(data)  # Print the entire response for debugging

    # Extract data for the second day (index 1)
    next_day = data["forecast"]["forecastday"][1]
    forecast_date = next_day["date"]
    day_data = next_day["day"]

    return {
        "city": city,
        "date": forecast_date,
        "min_temp": day_data["mintemp_c"],
        "max_temp": day_data["maxtemp_c"],
        "humidity": day_data["avghumidity"],
        "maxwind_kph": day_data["maxwind_kph"],
        # Wind direction for the day is taken from the averaged hourly data (e.g., at 12:00)
        "wind_dir": next_day["hour"][12]["wind_dir"]
    }


def main():
    if WEATHER_API_KEY == "YOUR_API_KEY":
        print("Error: Please specify a valid WEATHER_API_KEY in the environment variables.")
        return

    table_data = []
    target_date = None

    for city in CITIES:
        try:
            forecast = get_next_day_forecast(city, WEATHER_API_KEY)
            if not target_date:
                target_date = forecast["date"]

            table_data.append([
                forecast["city"],
                f"{forecast['min_temp']} °C",
                f"{forecast['max_temp']} °C",
                f"{forecast['humidity']} %",
                f"{forecast['maxwind_kph']} kph",
                forecast["wind_dir"]
            ])
        except requests.RequestException as e:
            print(f"Error fetching data for {city}: {e}")

    headers = [
        f"City / Date: {target_date}",
        "Min Temp (°C)",
        "Max Temp (°C)",
        "Humidity (%)",
        "Wind Speed (kph)",
        "Wind Direction"
    ]

    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))


if __name__ == "__main__":
    main()
