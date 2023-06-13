# Telegrambot-with-GPT4free
Simple telegram bot with [GPT4free](https://github.com/xtekky/gpt4free)   
Thanks to [xtekky](https://github.com/xtekky)  
Supports poe.com, thb.ai, you.com, deepai.org, AI Assist.   
Supports multiple bots in poe.com.   
Hugging face token is only required for image captioning.    
Support OCR with tesseract additional to [salesforce blip image captioning](https://huggingface.co/Salesforce/blip-image-captioning-large)    
If you want to use any other model change HG_img2text value
```
HG_img2text = 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large'    
```

Internet access using [duckduckgo_search](https://github.com/deedy5/duckduckgo_search)
Supports voice transcription with [openai whisper](https://github.com/openai/whisper)    
Image generation using [Imaginepy](https://github.com/ItsCEED/Imaginepy)

       

## Install


Download or clone this repository   
Change environment variables in .env file. [Environment Variables](#environment-variables)   
install the requirements(Install takes more time due to openai whisper package and its dependencies)    
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
Optional (leave it blank if you don't want to use quora(poe.com))
Sign up to Poe and head over to the site
ctrl+shift+i to open developer console
Go to Application -> Cookies -> https://poe.com
Find the p-b cookie and copy its value, this will be your Poe-token

`HG_TOKEN`
Optional(Required forimage captioning). Sign up on hugging face and get the token from [here](https://huggingface.co/settings/tokens)