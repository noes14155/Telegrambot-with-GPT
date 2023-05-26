# Telegrambot-with-GPT4free
Simple telegram bot with [GPT4free](https://github.com/xtekky/gpt4free)   
Thanks to [xtekky](https://github.com/xtekky)  
Supports poe.com, thb.ai, you.com   
Supports multiple bots in poe.com   
Hugging face token is only required for image captioning.    
Text to image (stable diffusion) uses hugging face hosted space feel free to change to your own space   
'''
HG_img2text = 'https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning'    
HG_text2img = 'https://noes14155-runwayml-stable-diffusion-v1-5.hf.space/'     
'''
line 15 and 16 in main.py


   
To do   
Add usesless   
Add forefront    

## Install


Download or clone this repository   
Change environment variables in .env file. [Environment Variables](#environment-variables)   
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
Not mandatory (leave it blank if you don't want to use quora(poe.com))
Sign up to Poe and head over to the site
ctrl+shift+i to open developer console
Go to Application -> Cookies -> https://poe.com
Find the p-b cookie and copy its value, this will be your Poe-token

`HG_TOKEN`
Sign up on hugging face and get the token from [here](https://huggingface.co/settings/tokens)