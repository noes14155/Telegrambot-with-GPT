import telebot
from gpt4free import quora
import os
import requests

BOT_TOKEN=os.environ['BOT_TOKEN']
POE_TOKEN=os.environ['POE_TOKEN']
#HG_TOKEN = os.environ['HG_TOKEN']
#HG_API = os.environ[HG_API]
#Create new instance of bot
bot = telebot.TeleBot(BOT_TOKEN)
#models avaiable a poe.com
models = {
    'Sage': 'capybara',
    'GPT-4': 'beaver',
    'Claude+': 'a2_2',
    'Claude-instant': 'a2',
    'ChatGPT': 'chinchilla',
    'Dragonfly': 'nutria',
    'NeevaAI': 'hutia',
}

#headers = {"Authorization": f"Bearer {HG_TOKEN}"}

api_name = 'quora'
model = 'ChatGPT'   
if POE_TOKEN == "":
   print('No POE-TOKEN found! Add it in your env file')
   exit
if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit

#function takes user prompt and poe model name, returns chat response
def stream(prompt,model): 
        text = ''    
        if api_name == 'quora':          
          for response in quora.StreamingCompletion.create(model=model,
                                                      prompt=prompt,
                                                      token=POE_TOKEN):
            #print(response.text, flush=True)
            text += str(response.text)
          return text
'''
def process_image(url):
    with open(url, "rb") as f:
        image = f.read()
    # Make POST request to API
    response = requests.post(HG_API, headers=headers, data=image)  
    caption = response.json()["captions"]
    return caption
'''
#selecting model handler
@bot.callback_query_handler(func=lambda call: True)
def model_selector(message):
    model=message.data
    bot.send_message( message.message.chat.id,model+' is active')
#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
def start_handler(update):
    bot.send_message(update.chat.id, text="Hello, Welcome to GPT4free")
#help command handler
@bot.message_handler(commands=['help'])
def help_handler(update):
    bot.send_message(update.chat.id, text="/start : starts the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
#changebot command handler
@bot.message_handler(commands=['changebot'])
def changebot_handler(message):
    inline_kb = telebot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        inline_kb.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    bot.send_message(message.chat.id,'Currently'+i+'is active'+' (gpt-4 and claude-v1.2 requires a paid subscription)', reply_markup=inline_kb)
#Messages other than commands handled 
@bot.message_handler(func=lambda message: True)
def reply_handler(update):
    '''
    image_caption = ""
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', 'webp')):
                #caption =  process_image(attachment.url)
                break
    '''
    # Send "typing" action  
    bot.send_chat_action(update.chat.id, "typing")
    try:
        text = stream(update.text,model)
    except: 
        text = "Sorry, I'm having issues."
    bot.send_message(update.chat.id,text)
bot.infinity_polling()

