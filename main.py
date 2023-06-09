
from telebot.async_telebot import AsyncTeleBot
import telebot
import asyncio
import aiohttp
import random
from gpt4free import quora
from gpt4free import you
from gpt4free import theb
from gpt4free import deepai
from gpt4free import aiassist
from bot import botfn
from bot import botdb
from bot import botocr
import os
from gradio_client import Client

BOT_TOKEN = os.environ['BOT_TOKEN']
POE_TOKEN = os.environ['POE_TOKEN']
HG_TOKEN = os.environ['HG_TOKEN']
#HG_API = os.environ[HG_API]
HG_img2text = 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large'
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
providers = ['deepai','you','AI Assist','theb','quora','Stable Diffusion(generate image)']
_missingpoetoken = ['Add now','Later']
headers = {"Authorization": f"Bearer {HG_TOKEN}"}
instruction_file = 'instructions.txt'
messages = [
    "Please wait...","Hang on a sec...","Just a moment...","Processing your request...",
    "Almost done...","Working on it...","One moment please...","Patience is a virtue...",
    "Hold tight...","Be right back...","We're on it...","Doing our thing...","Sit tight...",
    "Almost there...","Just a little longer...","Processing...","Stay put...",
]
bn = botfn.botfn()
db = botdb.Database('chatbot.db')
ocr = botocr.OCR(config=" --psm 3 --oem 3 -l script/Devanagari")
db.create_tables()
if os.path.exists(instruction_file):
    with open(instruction_file, 'r') as file:
        instruction = file.read()
else:
    print(f'{instruction_file} does not exist')

if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit

async def get_aiassist_response(prompt):
    completion = aiassist.Completion.create(prompt=prompt)
    response = completion['text']
    return response
#function takes user prompt, poe model name, provider name returns chat response
async def stream(call,model,api_name): 
        text = ''    
        global instruction
        result = db.get_settings(call.from_user.id)
        if result is None:
            api_name, model = 'AI Assist','ChatGPT'
            db.insert_settings(call.from_user.id, api_name, model)
        else:
            api_name, model = result
        rows = db.get_history(call.from_user.id)[-10:]
    
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
            history = []
            for row in rows:
                role, content = row
            messages.append({"role": role, "content": content})
            messages = [{"role": "user", "content": instruction},\
                        *history,
                        ]
            messages.append({"role": "user", "content":call.text})
            for chunk in deepai.ChatCompletion.create(messages):
                text += chunk 
        elif api_name == 'AI Assist':
            history=''
            prompt=instruction+'\n'+history+'\n'+call.text
            history = '\n'.join(row[1] for row in rows)
            text = await get_aiassist_response(prompt=prompt)
           
        elif api_name == 'Stable Diffusion(generate image)':
            client = Client(HG_text2img)
            text = client.predict(call.text,api_name="/predict")
        print(text)
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


async def download_audio_file_from_message(message):
    if message.audio is not None:
        audio_file = message.audio
    elif message.voice is not None:
        audio_file = message.voice
    else:
        return None
    file_path = f'{audio_file.file_id}.ogg'
    file_dir = 'audio_files'
    os.makedirs(file_dir, exist_ok=True)
    full_file_path = os.path.join(file_dir, file_path)
    file_info = await bot.get_file(message.voice.file_id)
    #await file_info.download(full_file_path)
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(full_file_path, 'wb') as new_file:
        new_file.write(downloaded_file)
    return full_file_path

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
async def send_with_waiting_message(chat_id):
    waiting_message = random.choice(messages)
    sent = await bot.send_message(chat_id, waiting_message)
    message_id = sent.message_id
    chat_action_task = asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    await asyncio.sleep(3) 
    await bot.delete_message(chat_id=chat_id, message_id=message_id)
#funtion to handle keyboards
@bot.callback_query_handler(func=lambda call: True)
async def option_selector(call):
    result = db.get_settings(call.from_user.id)
    if result is None:
        api_name, model = 'AI Assist','ChatGPT'
        db.insert_settings(call.from_user.id, api_name, model)
    else:
        api_name, model = result
    if call.data in _missingpoetoken:
        if str(call.data) == 'Add now':
            await bot.send_message(call.message.chat.id,'OK Sign up to Poe and head over to the site ctrl+shift+i\
                            to open developer console Go to Application -> Cookies -> https://poe.com \
                            Find the p-b cookie and copy its value, this will be your Poe-token. -> Enter it here')
            bot.register_next_step_handler(call.message, handle_poe_token)
        elif str(call.data) == 'Later':
            await bot.send_message(call.message.chat.id,'No POE-TOKEN found! Add it in your env file.\
                                 Reverting to you.com')
            api_name='you'
    if call.data in providers:        
        if api_name == 'quora':
            if POE_TOKEN == "":
                _missing_poe_token(call.message)
                return
        elif api_name == 'forefront':
            api_name = 'AI Assist'
            text = 'Not yet implemented. Changing provider to AI Assist'
            await bot.send_message(call.message.chat.id,text)
            return
        api_name = str(call.data)
        db.upate_settings(call.from_user.id,api_name=api_name)
        await bot.send_message( call.message.chat.id,api_name+' is active')
    elif call.data in models:
        model = str(call.data)
        await bot.send_message( call.message.chat.id,model+' is active')
        db.update_settings(call.from_user.id,model=model)
#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
async def start_handler(message):
    api_name = 'AI Assist'
    db.insert_settings(message.chat.id, 'AI Assist', 'ChatGPT')
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
    result = db.get_settings(message.from_user.id)
    if result is None:
        api_name, model = 'AI Assist','ChatGPT'
        db.insert_settings(message.from_user.id, api_name, model)
    else:
        api_name, model = result
    if api_name != 'quora':
        await bot.send_message(message.chat.id,'changebot command only available for poe')
        return
    _models = telebot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        _models.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    await bot.send_message(message.chat.id,'Select model to use', reply_markup=_models)
#changeprovider command handler
@bot.message_handler(commands=['changeprovider'])
async def changeprovider_handler(message):
    _providers = telebot.types.InlineKeyboardMarkup()
    for i in providers:
        _providers.add(telebot.types.InlineKeyboardButton(i, callback_data=i))
    await bot.send_message(message.chat.id,'Select which provider to use', reply_markup=_providers)
#Messages other than commands handled 
@bot.message_handler(content_types='text')
async def reply_handler(call):
    result = db.get_settings(call.from_user.id)
    if result is None:
        api_name, model = 'AI Assist','ChatGPT'
        db.insert_settings(call.from_user.id, api_name, model)
    else:
        api_name, model = result
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    try:
        text_task = asyncio.create_task(stream(call,model,api_name))
        text = await text_task
    except RuntimeError as error: 
        if " ".join(str(error).split()[:3]) == "Daily limit reached":
            text = "Daily Limit reached for current bot. please use another bot or another provider"
        else:
            text = str(error)
    if api_name == 'Stable Diffusion(generate image)':
        await bot.send_photo(chat_id=call.chat.id, photo=open(text, 'rb'))      
    else:
        db.insert_history(call.chat.id, 'user', call.text)
        db.insert_history(call.chat.id, 'assistant', text)
        message_task = asyncio.create_task(bot.send_message(call.chat.id,text))
        message = await message_task
#messages with audio or photo
@bot.message_handler(content_types=['voice', 'audio', 'photo'])
async def imageaudio_handler(call): 
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    if call.content_type == 'photo':
        file_info = await bot.get_file(call.photo[-1].file_id)
        image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        text = await process_image(image_url)
        await bot.send_message(call.chat.id,text)
        ocr_text = ocr.process_image(image_url)
        if ocr_text:
            prompt = instruction + '\n[System: This is a image context provided by an image to text model. Generate a caption with an appropriate response.]'\
                  + text + \
                  '\n[System: This is a image context provided by a OCR model which is not stable. If it\'s gibberish leave it out of your answer if its readable answer accordingly]'\
                  + ocr_text  
            text = text + ocr_text
            
        else:
            prompt = instruction + '\n[System: This is a image context provided by an image to text model. Generate a caption with an appropriate response.]' + text
      
    elif call.content_type == 'audio' or 'voice':
        audio_file_path = await download_audio_file_from_message(call)
        text = await bn.transcribe_audio(audio_file_path)
        sent = await bot.send_message(call.chat.id,'Transcribed audio:' + text)
        prompt = instruction+'\n[System: This is a transcription of the user\'s command provided by an voice to text model. May contain transcription errors reply accordingly]'+text
    else:
        return
    response = await get_aiassist_response(prompt)
    await bot.send_message(call.chat.id,response)
    db.insert_history(call.chat.id, 'user', text)
    db.insert_history(call.chat.id, 'assistant', response)

async def main():
    # Run the bot in the event loop
    await bot.polling()

if __name__ == '__main__':
    # Create a new event loop and run the main coroutine
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

db.close_connection()