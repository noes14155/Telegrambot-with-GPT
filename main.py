import telebot
from gpt4free import quora
from gpt4free import you
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
providers = ['quora','you']
#headers = {"Authorization": f"Bearer {HG_TOKEN}"}
api_name = 'you'
model = 'ChatGPT'   
if POE_TOKEN == "":
   print('No POE-TOKEN found! Add it in your env file')
   exit
if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit

#function takes user prompt and poe model name, returns chat response
def stream(prompt,model,api_name): 
        text = ''    
        if api_name == 'quora':          
          for response in quora.StreamingCompletion.create(model=model,
                                                      prompt=prompt,
                                                      token=POE_TOKEN):
            #print(response.text, flush=True)
            text += str(response.text)
        elif api_name == 'you':
          response = you.Completion.create(prompt=prompt, detailed=True, include_links=True)
          text = response.text
          print(text)
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
#selecting provider or model for quora handler
@bot.callback_query_handler(func=lambda call: True)
def option_selector(call):
    if call.data in providers:
        global api_name
        api_name=str(call.data)
        bot.send_message( call.message.chat.id,api_name+' is active')
        print(api_name)
    elif call.data in models:
        global model
        model = str(call.data)
        bot.send_message( call.message.chat.id,model+' is active')

#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
def start_handler(update):
    bot.send_message(update.chat.id, text="Hello, Welcome to GPT4free.\n Current provider:"+api_name+\
                     "\nUse command /changeprovider or /changebot to change to a different bot")
#help command handler
@bot.message_handler(commands=['help'])
def help_handler(update):
    bot.send_message(update.chat.id, text="/start : starts the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
#changebot command handler
@bot.message_handler(commands=['changebot'])
def changebot_handler(message):
    print(api_name)
    if api_name != 'quora':
        bot.send_message(message.chat.id,'changebot command only available for poe')
        return
    _models = telebot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        _models.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    bot.send_message(message.chat.id,'Currently '+model+' is active'+\
                     ' (gpt-4 and claude-v1.2 requires a paid subscription)', reply_markup=_models)
#changeprovider command handler
@bot.message_handler(commands=['changeprovider'])
def changeprovider_handler(message):
    #making buttons with the model dictionary 
    _providers = telebot.types.InlineKeyboardMarkup()
    for i in providers:
        _providers.add(telebot.types.InlineKeyboardButton(i, callback_data=i))
    bot.send_message(message.chat.id,'Currently '+api_name+' is active', reply_markup=_providers)

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
        text = stream(update.text,model,api_name)
    except: 
        text = "Sorry, I'm having issues."
    bot.send_message(update.chat.id,text)
bot.infinity_polling()

