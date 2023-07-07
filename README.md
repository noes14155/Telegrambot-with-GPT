# Telegrambot-with-GPT4free
Telegram bot with chatgpt. Aiogram API.       
Hugging face token is only required for image captioning.    
Support OCR with tesseract additional to [salesforce blip image captioning](https://huggingface.co/Salesforce/blip-image-captioning-large)    
If you want to use any other model change HG_img2text value. Change it in the environment variables.               
Support for multi language. Easy to translate to your own language.        
        

Internet access using [duckduckgo_search](https://github.com/deedy5/duckduckgo_search)
Supports voice transcription with [speec_recognition](https://github.com/Uberi/speech_recognition)    
Image generation using [Imaginepy](https://github.com/ItsCEED/Imaginepy)

       
Support for plugins duckduckgo search and news. Ask for latest news on a topic (Under testing).        

## Installation Steps


Download or clone this repository  
Go to the directory

```
git clone https://github.com/noes14155/Telegrambot-with-GPT4free
cd Telegrambot-with-GPT4free
```


Copy example.env file to .env

```
cp example.env .env
```

Change environment variables in .env file [Environment Variables](#environment-variables)   

```
nano .env
```


Create virtual environment for this project/directory     

```
python3 -m venv venv
source venv/bin/activate
```


Install the requirements    
```
apt install -y flac ffmpeg tesseract-ocr
wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/script/Devanagari.traineddata -P /usr/share/tesseract-ocr/4.00/tessdata/script/
EXPORT TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

pip install -r requirements.txt
```
Run the bot
```
python main.py
```
## Docker
Build (change environment variables before build)
```
docker build -t telegrambot_gpt4free:latest "." 
```
Docker-compose
```
docker-compose up --build -d
```



## Environment Variables

To run this project, you will need to create a .env file or rename the existing example.env to .env and add the following environment variables   

`BOT_TOKEN`
Get this by messaging @botfather Refer to https://core.telegram.org/bots/tutorial#obtain-your-bot-token

`HG_TOKEN`
Optional(Required for image captioning). Sign up on hugging face and get the token from [here](https://huggingface.co/settings/tokens)      
      
`HG_img2text`
Required for image captioning. If you wnat to use another model for image captioning. change it here.   
Default value HG_img2text = 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large'     

`DEFAULT_LANG`
Change to your language currently English and Russian supported. If you want to translate to your own language please do so in the language_files folder make your own language.yml file and add the language to languages.yml file.        
