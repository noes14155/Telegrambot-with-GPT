# Telegrambot-with-GPT4free
Simple telegram bot with GPT4free https://github.com/xtekky/gpt4free   
And poe-api by https://github.com/ading2210/poe-api
Currently only supports poe.com   
Supports multiple bots   

   
To do   
Add you.com   
Add forefront    

## Install


Download or clone this repository
change environment variables in .env file
install the requirements 
```
pip install -r requirements.txt
```
Run main.py
```
python main.py
```
## Docker

Docker-compose
```
docker-compose up --build -d
```



## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`BOT_TOKEN`
Get this by messaging @botfather Refer to https://core.telegram.org/bots/tutorial#obtain-your-bot-token

`POE_TOKEN`
Sign up to Poe and head over to the site
ctrl+shift+i to open developer console
Go to Application -> Cookies -> https://poe.com
Find the p-b cookie and copy its value, this will be your Poe-token

