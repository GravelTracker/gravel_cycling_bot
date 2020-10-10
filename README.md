# gravel_cycling_bot

`gravel_cycling_bot` is the repository that powers [/u/gravelcyclingbot](https://reddit.com/u/gravelcyclingbot) on the [/r/gravelcycling subreddit](https://reddit.com/r/gravelcycling). 

## Functions

- Scrape data from the [GravelCyclist event calendar](https://gravelcyclist.com/)
- Interface with the user front end app [GravelTracker](http://graveltracker.com) to allow user uploads
- Build a monthly post with all upcoming events for the current month and sticky it
- Report its uptime statistics to GravelTracker
- \[DEPRECATED] Scrape bike data and allow user comparisons of bike frames/parts via Reddit (feature removed and added to [`gravel_cycling_bike_scraper`](https://github.com/GravelTracker/gravel_cycling_bike_scraper))

## Tech

`gravel_cycling_bot` interfaces with a MongoDB backend to create event and notification data. Once per month, events for the upcoming month are listed in a table. GravelTracker handles user additions, and when one is created a corresponding `notification` record is also created. If `gravel_cycling_bot` notices a new notification, it is capable of re-polling event data to update the stickied post with the new user addition.

Similarly, to facilitate displaying uptime statistics on GravelTracker, `gravel_cycling_bot` also periodically polls the database with a `status` record to indicate that it is up and working, and GravelTracker is capable of displaying a timeline of any adverse events to the bot.