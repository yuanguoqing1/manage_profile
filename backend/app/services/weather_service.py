"""天气服务 - 高德天气API"""

import os
import httpx

AMAP_KEY = os.getenv("AMAP_WEB_SERVICE_KEY", "")


def get_weather_by_city(city: str = "") -> str:
    """通过高德API获取天气
    
    Args:
        city: 城市名称
        
    Returns:
        天气描述字符串，如 "晴 25°C"
    """
    if not AMAP_KEY or not city:
        return ""
    try:
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={AMAP_KEY}&city={city}&extensions=base"
        resp = httpx.get(url, timeout=5)
        data = resp.json()
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            return f"{live.get('weather', '晴')} {live.get('temperature', '')}°C"
    except Exception:
        pass
    return ""
