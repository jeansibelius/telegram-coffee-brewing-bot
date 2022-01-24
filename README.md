# Coffee brewing bot for Telegram

Based on [Telebot](https://github.com/yukuku/telebot).  
Runs on Google App Engine.

## How to run
- In `app.yaml` change the `YOUR_APP_ID_HERE` to your Google Cloud project ID.
- In `main.py` env var `TOKEN` required (bot token from Telegram bot father). 
- Deploy to GCP.
- In your browser, go to https://`project-id`.appspot.com/me (replace `project-id` with your project ID). Wait until you see a long text with `"ok": true` and your bot's name (might take a moment).
- Go to https://`project-id`.appspot.com/set_webhook?url=https://`project-id`.appspot.com/webhook (replace both `project-id`s with the Project ID). You should see `Webhook was set`.
- Open your Telegram client and send the message `/start` to your bot. (type @`your-bot-username` at the search field to initiate the conversation)
