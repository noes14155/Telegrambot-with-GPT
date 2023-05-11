# Telegrambot-with-GPT4free
Simple telegram bot with [GPT4free](https://github.com/xtekky/gpt4free)   
Thanks to [xtekky](https://github.com/xtekky)  
Supports poe.com, thb.ai, you.com   
Supports multiple bots in poe.com   

   
To do   
Add usesless   
Add forefront    

## Install


Download or clone this repository
Change environment variables in .env file. [Environment Variables](Environment Variables)
install the requirements 
```
pip install -r requirements.txt
```
Run main.py
```
python main.py
```
## Docker
Build
```
docker build -t telegrambot_gpt4free:latest "." 
```
Docker-compose
```
docker-compose up --build -d
```



## Environment Variables

To run this project, you will need to create a .env file and add the following environment variables   

`BOT_TOKEN`
Get this by messaging @botfather Refer to https://core.telegram.org/bots/tutorial#obtain-your-bot-token

`POE_TOKEN`
Sign up to Poe and head over to the site
ctrl+shift+i to open developer console
Go to Application -> Cookies -> https://poe.com
Find the p-b cookie and copy its value, this will be your Poe-token

