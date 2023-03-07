# oglaf-feed-bot

Checks for updates on oglaf.com (weekly) and broadcasts new strips to subscribers on Telegram

## Rationale:
- Using RSS is inconvenient, as it only fetches a title and thumbnail of a comic,
- Using original website is inconvenient, as it lacks mobile version and has (poor) pagination

## Running:
- Telegram token is passed as an environment variable BOT_TOKEN
- Admin user ID is passed as an environment variable ADMIN
- If running in Docker, pass your local timezone to the container using TZ environment variable
