from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins= ["*"]
)

cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

URL = "https://api.open-meteo.com/v1/forecast"

def fetchResponse(latitude, longitude):
    params = {
	"latitude": latitude,
	"longitude": longitude,
	"daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"]
}
    responses = openmeteo.weather_api(URL, params=params)
    return responses[0]

def getData(latitude, longitude):
    response = fetchResponse(latitude, longitude)
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["weather_code"] = daily_weather_code
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min

    daily_dataframe = pd.DataFrame(data = daily_data)
    return daily_dataframe


@app.get("/")
def requestData(latitude, longitude):
    response = getData(latitude, longitude) 

    return response.to_json(orient="records")