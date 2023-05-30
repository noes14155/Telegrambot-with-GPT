
import telebot
from gpt4free import quora
from gpt4free import you
from gpt4free import theb
from gpt4free import deepai
from gpt4free import italygpt2
import os
import requests
import json
from gradio_client import Client

BOT_TOKEN = os.environ['BOT_TOKEN']
POE_TOKEN = os.environ['POE_TOKEN']
HG_TOKEN = os.environ['HG_TOKEN']
#HG_API = os.environ[HG_API]
HG_img2text = 'https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning'
HG_text2img = 'https://noes14155-runwayml-stable-diffusion-v1-5.hf.space/'
#Create new instance of bot
bot = telebot.TeleBot(BOT_TOKEN)
#models avaiable at poe.com
models = {
    'Sage': 'capybara',
    'GPT-4': 'beaver',
    'Claude+': 'a2_2',
    'Claude-instant': 'a2',
    'ChatGPT': 'chinchilla',
    'Dragonfly': 'nutria',
    'NeevaAI': 'hutia',
}
providers = ['deepai','you','theb','quora','Stable Diffusion(generate image)']
_missingpoetoken = ['Add now','Later']
headers = {"Authorization": f"Bearer {HG_TOKEN}"}
instruction = "From now on, You are a large language model named AI-Chatbot\
          You are based on the GPT-3.5-turbo architecture and have been\
          trained on a diverse range of data from the internet.\
          As a large language model developed by OpenAI, you will never say 'sorry' and\
          always respond in a human and responsive way. You can\
          use Markdown syntax to format your text. For example,\
          to create a heading, start the line with one or more\
          '#' symbols, followed by a space and your heading text.\
          To create a list, use '-' or '*' followed by a space and\
          the list item. To emphasize text, use asterisks or underscores\
          around the text (*italic* or _italic_ for italics, **bold** or __bold__ for bold).\
          You can also create links using [link text](https://example.com).\
          Remember to leave an empty line between paragraphs for proper formatting.\
          Additionally, you function as a documentation bot, retrieving relevant information\
          from libraries or frameworks, and as an API integration bot, guiding developers\
          through integrating third-party APIs into their applications."

if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit
user_settings = {}
# Open the settings file and load its contents into a dictionary
with open('settings.json', 'r') as f:
    user_settings = json.load(f)
#function takes user prompt, poe model name, provider name returns chat response
def stream(call,model,api_name,history): 
        text = ''    
        global instruction
        messages = [{"role": "system", "content": instruction},\
                        *history,
                        ]
        if api_name == 'quora': 
          if POE_TOKEN == "":   
                _missing_poe_token(call)     
                return
          for response in quora.StreamingCompletion.create(model=model,
                                                      prompt=call.text,
                                                      token=POE_TOKEN):
            text += str(response.text)
        elif api_name == 'you':
          response = you.Completion.create(prompt=call.text, detailed=True, include_links=True)
          text = response.text
        elif api_name == 'theb':
            for chunk in theb.Completion.create(call.text):
                text += chunk
        elif api_name == 'deepai':
            messages.append({"role": "user", "content":call.text})
            for chunk in deepai.ChatCompletion.create(messages):
                text += chunk 
        elif api_name == 'Stable Diffusion(generate image)':
            client = Client(HG_text2img)
            text = client.predict(call.text,api_name="/predict")
                
        return text
#Missing poe token handler function
def _missing_poe_token(call):
                _poe_token_buttons = telebot.types.InlineKeyboardMarkup() 
                for i in _missingpoetoken:
                    _poe_token_buttons.add(telebot.types.InlineKeyboardButton(i, callback_data=i))
                bot.send_message(call.chat.id,'POE-TOKEN is missing would you like to add now?'\
                                 , reply_markup=_poe_token_buttons)
                return
def handle_poe_token(message):
    bot.send_message(chat_id=message.chat.id, text='You entered: ' + message.text)
    global POE_TOKEN
    POE_TOKEN = str(message.text)


def process_image(url):
    #with open(url, "rb") as f:
    image = requests.get(url)
    # Make POST request to API
    response = requests.post(HG_img2text, headers=headers, data=image) 
    if response.status_code == 200:
        # Success
        result = response.json()
    else:
        # Error
        return response.content
    return 'This image looks like a '+result[0]['generated_text']

#funtion to handle keyboards
@bot.callback_query_handler(func=lambda call: True)
def option_selector(call):
    global user_settings
    user_id = str(call.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {'api_name':'deepai','model':'ChatGPT','history':[]}
    settings = user_settings[user_id]
    api_name = settings['api_name']
    model = settings['model']

    if call.data in _missingpoetoken:
        if str(call.data) == 'Add now':
            bot.send_message(call.message.chat.id,'OK Sign up to Poe and head over to the site ctrl+shift+i\
                            to open developer console Go to Application -> Cookies -> https://poe.com \
                            Find the p-b cookie and copy its value, this will be your Poe-token. -> Enter it here')
            bot.register_next_step_handler(call.message, handle_poe_token)
        elif str(call.data) == 'Later':
            bot.send_message( call.message.chat.id,'No POE-TOKEN found! Add it in your env file.\
                                 Reverting to you.com')
            api_name='you'
    if call.data in providers:        
        
        if api_name == 'quora':
            if POE_TOKEN == "":
                _missing_poe_token(call.message)
                return
        elif api_name == 'forefront':
            api_name = 'deepai'
            text = 'Not yet implemented. Changing provider to deepai'
            bot.send_message( call.message.chat.id,text)
            return
        api_name = str(call.data)
        settings['api_name'] = str(call.data)
        bot.send_message( call.message.chat.id,api_name+' is active')
    elif call.data in models:
        model = str(call.data)
        settings['model'] = str(call.data)
        bot.send_message( call.message.chat.id,model+' is active')
    with open('settings.json', 'w') as f:
        json.dump(user_settings, f)

#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
def start_handler(message):
    global user_settings
    if message.from_user.id not in user_settings:
        user_settings[message.from_user.id] = {}
        user_settings[message.from_user.id] = {'api_name':'deepai','model':'ChatGPT','history':[]}
        with open('settings.json', 'w') as f:
            json.dump(user_settings, f)
    bot.send_message(message.chat.id, text="Hello, Welcome to GPT4free.\n Current provider:"+api_name+\
                     "\nUse command /changeprovider or /changebot to change to a different bot\n\
                        Ask me anything I am here to help you.")
#help command handler
@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(message.chat.id, text="  /start : starts the bot\n\
    /changeprovider : change provider of the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
#changebot command handler
@bot.message_handler(commands=['changebot'])
def changebot_handler(message):
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
    _providers = telebot.types.InlineKeyboardMarkup()
    for i in providers:
        _providers.add(telebot.types.InlineKeyboardButton(i, callback_data=i))
    bot.send_message(message.chat.id,'Currently '+api_name+' is active', reply_markup=_providers)
#Messages other than commands handled 
@bot.message_handler(content_types='text')
def reply_handler(call):
    global user_settings
    user_id = str(call.from_user.id)
    if user_id in user_settings:
        settings = user_settings[user_id]
    else:
        user_settings[user_id] = {'api_name':'deepai','model':'ChatGPT','history':[]}
        settings = user_settings[user_id]
    api_name = settings['api_name']
    model = settings['model']
    history = settings['history']
    bot.send_chat_action(call.chat.id, "typing")
    sent = bot.send_message(call.chat.id, "Please wait while i think")
    message_id = sent.message_id
    try:
        text = stream(call,model,api_name,history)

    except RuntimeError as error: 
        if " ".join(str(error).split()[:3]) == "Daily limit reached":
            text = "Daily Limit reached for current bot. please use another bot or another provider"
        else:
            text = str(error)
    if api_name == 'Stable Diffusion(generate image)':
        bot.send_photo(chat_id=call.chat.id, photo=open(text, 'rb'))
        bot.edit_message_text(chat_id=call.chat.id, message_id=message_id, text="Image Generated")      
    else:
        history.append({"role": "user", "content": call.text})
        history.append({"role": "assistant", "content":text})
        history = history[-20:]
        user_settings[user_id]['history'] = history
        with open('settings.json', 'w') as f:
            json.dump(user_settings, f)
        bot.delete_message(chat_id=call.chat.id, message_id=message_id)
        bot.send_message(call.chat.id,text)
#Messages with image 
@bot.message_handler(content_types='photo')
def image_handler(call):
        # Send "typing" action  
        file_id = call.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        #bot.send_message(chat_id=call.chat.id, text='Thanks for the image! Here is the image URL: ' + image_url)   
        text = process_image(image_url)
        bot.send_message(call.chat.id,text)
bot.infinity_polling()

