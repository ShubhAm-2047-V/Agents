"""
live_lookups.py
Provides real-world live data lookups & scrapers:
- Weather widgets (live temperature, condition, humidity, forecast)
- Flight searches (routes, airlines, durations, prices)
- Price tracking & comparison across retailers
- Crypto gas & transaction fees (Ethereum & Bitcoin)
"""

import re
import requests
import config
import search_backend

try:
    from google import genai
except ImportError:
    genai = None


def _get_client():
    if genai and config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE":
        return genai.Client(api_key=config.GEMINI_API_KEY)
    return None


def get_weather(city: str = "London") -> str:
    """
    Fetches real-time weather information and 3-day forecast for any city worldwide.
    """
    clean_city = city.strip()
    if clean_city.lower().startswith("in "):
        clean_city = clean_city[3:].strip()
    if clean_city.lower().startswith("for "):
        clean_city = clean_city[4:].strip()

    try:
        # Fetch json from wttr.in
        url = f"https://wttr.in/{requests.utils.quote(clean_city)}?format=j1"
        res = requests.get(url, timeout=6)
        if res.status_code == 200:
            data = res.json()
            current = data.get("current_condition", [{}])[0]
            temp_c = current.get("temp_C", "--")
            temp_f = current.get("temp_F", "--")
            desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
            humidity = current.get("humidity", "--")
            wind_kmh = current.get("windspeedKmph", "--")
            feels_c = current.get("FeelsLikeC", "--")

            # Weather icon
            desc_lower = desc.lower()
            icon = "☀️"
            if "rain" in desc_lower or "drizzle" in desc_lower:
                icon = "🌧️"
            elif "cloud" in desc_lower or "overcast" in desc_lower:
                icon = "☁️"
            elif "snow" in desc_lower:
                icon = "❄️"
            elif "thunder" in desc_lower or "storm" in desc_lower:
                icon = "⛈️"
            elif "fog" in desc_lower or "mist" in desc_lower:
                icon = "🌫️"

            # 3-day forecast
            forecast_lines = []
            weather_days = data.get("weather", [])
            for day in weather_days[:3]:
                date = day.get("date", "")
                min_c = day.get("mintempC", "")
                max_c = day.get("maxtempC", "")
                day_desc = day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "")
                forecast_lines.append(f"• {date}: {min_c}°C - {max_c}°C ({day_desc})")

            forecast_str = "\n".join(forecast_lines)

            return f"""🌤️ WEATHER REPORT: {clean_city.title()}
────────────────────────────────────────────────────────────
{icon} Condition: {desc}
🌡️ Temperature: {temp_c}°C / {temp_f}°F (Feels like {feels_c}°C)
💧 Humidity: {humidity}%
💨 Wind Speed: {wind_kmh} km/h

📅 3-DAY FORECAST:
{forecast_str}
────────────────────────────────────────────────────────────"""
    except Exception:
        pass

    # Fallback to search + Gemini
    search_res = search_backend.search_web(f"{clean_city} current weather forecast temperature", max_results=3)
    if not search_res:
        return f"⚠️ Could not fetch weather data for '{clean_city}'."

    client = _get_client()
    if client:
        sources_text = "\n".join(f"{r['title']}: {r['snippet']}" for r in search_res)
        prompt = f"Summarize current weather for {clean_city} in a clean terminal card with condition, temp, humidity, and forecast.\n\nData:\n{sources_text}"
        res = client.models.generate_content(model=config.MODEL, contents=prompt)
        return res.text.strip()

    return "\n".join(f"• {r['title']}: {r['snippet']}" for r in search_res)


def flight_search(origin: str, dest: str, date: str = "") -> str:
    """
    Searches for live flight routes, major airlines, estimated travel times, and fare ranges.
    """
    query = f"flights from {origin} to {dest} {date}".strip()
    results = search_backend.search_web(f"{query} flight duration price airlines", max_results=4)

    if not results:
        return f"⚠️ No flight information found for {origin} to {dest}."

    client = _get_client()
    if not client:
        return f"✈️ Flights: {origin.title()} to {dest.title()}\n\n" + "\n".join(f"• {r['title']}\n  {r['snippet']}\n  {r['url']}" for r in results)

    sources_text = "\n\n".join(f"[{i+1}] {r['title']}\n{r['snippet']}\nURL: {r['url']}" for i, r in enumerate(results))
    prompt = f"""You are a flight intelligence assistant. Present clean, structured travel intelligence for a command line terminal.

ROUTE: {origin} to {dest} {f'on {date}' if date else ''}
SOURCES:
{sources_text}

FORMATTING RULES:
1. Do not use markdown tables.
2. Structure strictly as:

✈️ ROUTE OVERVIEW
• Typical Flight Duration: (e.g. 7h 45m non-stop)
• Estimated Economy Fare Range: (e.g. $450 - $780)

🛫 TOP AIRLINES OPERATING
• Airline 1 (Direct / 1-stop options)
• Airline 2 (Direct / 1-stop options)

💡 BOOKING TIP & BEST TIME TO FLY
(1-2 actionable recommendations)

🔗 BOOKING PORTALS
[1] Title (domain.com)
"""
    try:
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error analyzing flights: {e}"


def price_tracker(product: str) -> str:
    """
    Searches e-commerce platforms (Amazon, Best Buy, Walmart) for product pricing and deals.
    """
    query = f"{product} price buy online amazon bestbuy walmart"
    results = search_backend.search_web(query, max_results=4)

    if not results:
        return f"⚠️ No current price listings found for '{product}'."

    client = _get_client()
    if not client:
        return f"🏷️ Price listings for '{product}':\n\n" + "\n".join(f"• {r['title']}: {r['snippet']}\n  {r['url']}" for r in results)

    sources_text = "\n\n".join(f"[{i+1}] {r['title']}\n{r['snippet']}\nURL: {r['url']}" for i, r in enumerate(results))
    prompt = f"""You are a price comparison expert. Structure current prices and availability for a CLI terminal.

PRODUCT: {product}
SOURCES:
{sources_text}

FORMATTING RULES:
1. Do not use markdown tables.
2. Structure strictly as:

🏷️ PRICE INTELLIGENCE: {product.title()}
• Typical Market Price Range: (e.g. $399 - $449)
• Best Deals Detected: (List retailers and price points found)

🔍 RETAILER BREAKDOWN
• Retailer 1: Price and key bundle/warranty note
• Retailer 2: Price and key bundle/warranty note

💡 BUYING ADVICE
(Is it a good time to buy, or should the user wait for discounts?)

🔗 STORE LINKS
[1] Title (domain.com)
"""
    try:
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error checking prices: {e}"


def crypto_gas_fees() -> str:
    """
    Fetches real-time Ethereum gas prices (Gwei) and Bitcoin transaction fees.
    """
    try:
        # Fetch ETH gas from etherscan public gas oracle or ethgasstation fallback
        res = requests.get("https://api.blocknative.com/gasprices/blockprices", timeout=4)
        # Or search for latest gas
    except Exception:
        pass

    results = search_backend.search_web("ethereum gas gwei price bitcoin sat vb fee current", max_results=3)
    client = _get_client()
    if not client:
        return "⛽ CRYPTO GAS & FEES\n\n" + "\n".join(f"• {r['title']}: {r['snippet']}" for r in results)

    sources_text = "\n\n".join(f"{r['title']}: {r['snippet']}" for r in results)
    prompt = f"""Extract and format current Ethereum gas fees and Bitcoin transaction fees into a clean terminal status report.

SOURCES:
{sources_text}

Structure as:
⛽ ETHEREUM GAS (GWEI)
• Low / Standard / Fast transfer costs (and estimated USD transfer fee for ERC-20 swap)

⚡ BITCOIN FEES (SAT/VB)
• Current recommended sat/vB for next block vs low priority

💡 TIMING TIP
(Best hours/days for low network congestion)
"""
    try:
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error checking gas fees: {e}"
