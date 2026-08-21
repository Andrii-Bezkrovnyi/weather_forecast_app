# Weather Forecast App

A small command-line application that fetches tomorrow's weather forecast from WeatherAPI.com.

### Features
- Asynchronous HTTP requests with httpx
- Response validation with pydantic (robust parsing)
- Logs written to both console (stderr) and a file (weather_forecast.log)
- Unit tests that use httpx.MockTransport (no real API calls)

### Requirements
- Python 3.8+ (3.10/3.11 recommended)
- See requirements.txt for runtime and test dependencies

### Installation (Windows)
1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
- ```bash
  .\venv\Scripts\Activate.ps1   # PowerShell
   ```
- ```bash
  venv\Scripts\activate.bat   # cmd.exe
  ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
1. Copy .env.example to .env and set your API key:
  - ```bash
    copy .env.example .env
    ```
  - Edit .env and set **`WEATHER_API_KEY=your_api_key_here`**

2. Available settings (environment variables / pydantic Settings):
   - WEATHER_API_KEY (required)
   - WEATHER_API_BASE_URL (default: https://api.weatherapi.com/v1/forecast.json)
   - REQUEST_TIMEOUT (seconds, default: 10.0)
   - FORECAST_DAYS (default: 2)
   - WIND_DIR_HOUR (hour used for wind direction, default: 12)

### Running code
From the project root:
```bash
   python main.py
```
The app fetches forecasts for a predefined list of cities and prints a table to the console.

Logging
- Console: stderr (INFO and above)
- File: weather_forecast.log in the repository root (UTF-8)

### Tests
Run tests with:
```bash
    python -m pytest -v
```
Tests use httpx.MockTransport, so no real HTTP requests are performed.

### Development
- Package: weather_forecast/
- Entry point: main.py --> weather_forecast.cli.main()
