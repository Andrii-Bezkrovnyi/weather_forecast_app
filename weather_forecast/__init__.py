"""weather_forecast: fetch and display next-day WeatherAPI.com forecasts.

Package layout:
    config.py    - typed settings (pydantic-settings), reads .env
    models.py    - pydantic models for the WeatherAPI.com response + our own domain model
    client.py    - async httpx client: fetch + validate one city's forecast
    service.py   - orchestration: fetch all cities concurrently, collect results
    display.py   - render the results as a rich table
    cli.py       - composition root: wires the above together into main()

The root-level main.py just calls weather_forecast.cli.main().
"""
