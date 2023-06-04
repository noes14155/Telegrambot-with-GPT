
from telebot.async_telebot import AsyncTeleBot
import asyncio
import aiohttp
import aiofiles
from gpt4free import quora
from gpt4free import you
from gpt4free import theb
from gpt4free import deepai
from gpt4free import aiassist
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
bot = AsyncTeleBot(BOT_TOKEN)
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
providers = ['deepai','you','world','theb','quora','Stable Diffusion(generate image)']
_missingpoetoken = ['Add now','Later']
model = ''
api_name=''
headers = {"Authorization": f"Bearer {HG_TOKEN}"}
instruction_file = 'instructions.txt'

if os.path.exists(instruction_file):
    with open(instruction_file, 'r') as file:
        instruction = file.read()
else:
    print(f'{instruction_file} does not exist')

if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit
user_settings = {}
# Open the settings file and load its contents into a dictionary
with open('settings.json', 'r') as f:
    user_settings = json.load(f)
#function takes user prompt, poe model name, provider name returns chat response
async def stream(call,model,api_name,history): 
        text = ''    
        global instruction
        global user_settings
        user_id = str(call.from_user.id)
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
        elif api_name == 'world':
            completion = aiassist.Completion.create(prompt=call.text,\
                                                    parentMessageId=user_settings[user_id]['message_id'])            
            text = completion['text']
            print(text)
           
        elif api_name == 'Stable Diffusion(generate image)':
            client = Client(HG_text2img)
            text = client.predict(call.text,api_name="/predict")
                
        return text
#Missing poe token handler function
async def _missing_poe_token(call):
                _poe_token_buttons = AsyncTeleBot.types.InlineKeyboardMarkup() 
                for i in _missingpoetoken:
                    _poe_token_buttons.add(AsyncTeleBot.types.InlineKeyboardButton(i, callback_data=i))
                await bot.send_message(call.chat.id,'POE-TOKEN is missing would you like to add now?'\
                                 , reply_markup=_poe_token_buttons)
                return
async def handle_poe_token(message):
    await bot.send_message(chat_id=message.chat.id, text='You entered: ' + message.text)
    global POE_TOKEN
    POE_TOKEN = str(message.text)

async def save_user_settings(user_settings):
    async with aiofiles.open('settings.json', 'w') as f:
        await f.write(json.dumps(user_settings))

async def process_image(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image = await resp.read()
        async with session.post(HG_img2text, headers=headers, data=image) as resp:
            if resp.status == 200:
                result = await resp.json()
                return 'This image looks like a ' + result[0]['generated_text']
            else:
                return await resp.content.read()

#funtion to handle keyboards
@bot.callback_query_handler(func=lambda call: True)
async def option_selector(call):
    global user_settings
    global instruction
    user_id = str(call.from_user.id)
    if user_id not in user_settings:
        user_settings[user_id] = {'api_name':'deepai','model':'ChatGPT','history':[],'message_id':''}
    settings = user_settings[user_id]
    api_name = settings['api_name']
    model = settings['model']

    if call.data in _missingpoetoken:
        if str(call.data) == 'Add now':
            await bot.send_message(call.message.chat.id,'OK Sign up to Poe and head over to the site ctrl+shift+i\
                            to open developer console Go to Application -> Cookies -> https://poe.com \
                            Find the p-b cookie and copy its value, this will be your Poe-token. -> Enter it here')
            bot.register_next_step_handler(call.message, handle_poe_token)
        elif str(call.data) == 'Later':
            await bot.send_message( call.message.chat.id,'No POE-TOKEN found! Add it in your env file.\
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
            await bot.send_message(call.message.chat.id,text)
            return
        elif api_name == 'world':
            if(user_settings[user_id]['message_id'] == ''):
                completion = aiassist.Completion.create(prompt=instruction)
                settings['message_id'] = completion['parentMessageId']
                print(completion['text'])
        api_name = str(call.data)
        settings['api_name'] = str(call.data)
        await bot.send_message( call.message.chat.id,api_name+' is active')
    elif call.data in models:
        model = str(call.data)
        settings['model'] = str(call.data)
        await bot.send_message( call.message.chat.id,model+' is active')
    user_settings[user_id] = settings
    await save_user_settings(user_settings)

#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
async def start_handler(message):
    global user_settings
    if str(message.from_user.id) not in user_settings:
        user_settings[message.from_user.id] = {}
        user_settings[message.from_user.id] = {'api_name':'deepai','model':'ChatGPT','history':[],'message_id':''}
        await save_user_settings(user_settings)
    await bot.send_message(message.chat.id, text="Hello, Welcome to GPT4free.\n Current provider:"+api_name+\
                     "\nUse command /changeprovider or /changebot to change to a different bot\n\
                        Ask me anything I am here to help you.")
#help command handler
@bot.message_handler(commands=['help'])
async def help_handler(message):
    await bot.send_message(message.chat.id, text="  /start : starts the bot\n\
    /changeprovider : change provider of the bot\n\
    /changebot : change to available bots in poe.com\n\
    /help : list all commands")
#changebot command handler
@bot.message_handler(commands=['changebot'])
async def changebot_handler(message):
    api_name = user_settings[message.from_user.id]['api_name']
    model = user_settings[message.from_user.id]['api_name']
    if api_name != 'quora':
        await bot.send_message(message.chat.id,'changebot command only available for poe')
        return
    _models = AsyncTeleBot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        _models.add(AsyncTeleBot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    await bot.send_message(message.chat.id,'Currently '+model+' is active'+\
                     ' (gpt-4 and claude-v1.2 requires a paid subscription)', reply_markup=_models)
#changeprovider command handler
@bot.message_handler(commands=['changeprovider'])
async def changeprovider_handler(message):
    _providers = AsyncTeleBot.types.InlineKeyboardMarkup()
    for i in providers:
        _providers.add(AsyncTeleBot.types.InlineKeyboardButton(i, callback_data=i))
    await bot.send_message(message.chat.id,'Currently '+api_name+' is active', reply_markup=_providers)
#Messages other than commands handled 
@bot.message_handler(content_types='text')
async def reply_handler(call):
    global user_settings
    user_id = str(call.from_user.id)
    if user_id in user_settings:
        settings = user_settings[user_id]
    else:
        user_settings[user_id] = {'api_name':'deepai','model':'ChatGPT','history':[],'message_id':''}
        settings = user_settings[user_id]
    api_name = settings['api_name']
    model = settings['model']
    history = settings['history']
    await bot.send_chat_action(call.chat.id, "typing")
    sent = await bot.send_message(call.chat.id, "Please wait while i think")
    message_id = sent.message_id
    try:
        text = await stream(call,model,api_name,history)

    except RuntimeError as error: 
        if " ".join(str(error).split()[:3]) == "Daily limit reached":
            text = "Daily Limit reached for current bot. please use another bot or another provider"
        else:
            text = str(error)
    if api_name == 'Stable Diffusion(generate image)':
        await bot.send_photo(chat_id=call.chat.id, photo=open(text, 'rb'))
        await bot.edit_message_text(chat_id=call.chat.id, message_id=message_id, text="Image Generated")      
    else:
        history.append({"role": "user", "content": call.text})
        history.append({"role": "assistant", "content":text})
        history = history[-20:]
        user_settings[user_id]['history'] = history
        await save_user_settings(user_settings)
        await bot.delete_message(chat_id=call.chat.id, message_id=message_id)
        await bot.send_message(call.chat.id,text)
#Messages with image 
@bot.message_handler(content_types='photo')
async def image_handler(call): 
        file_id = call.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_path}"
        #await bot.send_message(chat_id=call.chat.id, text='Thanks for the image! Here is the image URL: ' + image_url)   
        text = await process_image(image_url)
        await bot.send_message(call.chat.id,text)
async def main():
    # Run the bot in the event loop
    await bot.polling()

if __name__ == '__main__':
    # Create a new event loop and run the main coroutine
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

