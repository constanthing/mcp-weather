from pydantic import BaseModel
from typing import Optional

class Request(BaseModel):
    prompt: str
    model: Optional[str] = "gemini-2.5-flash"
    temperature: float = 0.3
    
class WeatherData(BaseModel):
    response_time: float
    location: str
    state: str
    forecast_days: Optional[int] = 1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None 
    data: list[dict]