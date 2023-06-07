
from telebot.async_telebot import AsyncTeleBot
import telebot
import asyncio
import aiohttp
import sqlite3
from gpt4free import quora
from gpt4free import you
from gpt4free import theb
from gpt4free import deepai
from gpt4free import aiassist
import botfn
import os
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
providers = ['deepai','you','AI Assist','theb','quora','Stable Diffusion(generate image)']
_missingpoetoken = ['Add now','Later']
model = ''
api_name=''
headers = {"Authorization": f"Bearer {HG_TOKEN}"}
instruction_file = 'instructions.txt'
bn = botfn.botfn()

if os.path.exists(instruction_file):
    with open(instruction_file, 'r') as file:
        instruction = file.read()
else:
    print(f'{instruction_file} does not exist')

if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit
# Connect to the SQLite database
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Create the settings table if it doesn't exist yet
c.execute('''CREATE TABLE IF NOT EXISTS settings 
             (user_id INTEGER PRIMARY KEY, api_name TEXT, model TEXT, message_id TEXT)''')

# Create the history table if it doesn't exist yet
c.execute('''CREATE TABLE IF NOT EXISTS history 
             (user_id INTEGER, role TEXT, content TEXT)''')
    #function takes user prompt, poe model name, provider name returns chat response
async def stream(call,model,api_name): 
        text = ''    
        global instruction
        c.execute('''SELECT * FROM settings WHERE user_id=?''', (call.from_user.id,))
        row = c.fetchone()
        if row:
            user_id, api_name, model, message_id = row
        else:
            user_id, api_name, model, message_id = call.from_user.id,'deepai','ChatGPT',''
        c.execute('''SELECT role, content FROM history WHERE user_id=?''', (call.from_user.id,))
        rows = c.fetchall()
    
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
            for role,content in rows[10:]:
                
                print(content)
                history = history + '\n' + content
            completion = aiassist.Completion.create(prompt=instruction+history+'\n'+call.text)     
            text = completion['text']
           
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

#funtion to handle keyboards
@bot.callback_query_handler(func=lambda call: True)
async def option_selector(call):
    c.execute('''SELECT * FROM settings WHERE user_id=?''', (call.from_user.id,))
    row = c.fetchone()
    if row:
        user_id, api_name, model, message_id = row
    else:
        user_id, api_name, model, message_id = call.from_user.id, 'deepai', 'ChatGPT', ''
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
            api_name = 'deepai'
            text = 'Not yet implemented. Changing provider to deepai'
            await bot.send_message(call.message.chat.id,text)
            return
        elif api_name == 'AI Assist':
            if message_id == '':
                completion = aiassist.Completion.create(prompt=instruction)
                message_id = completion['parentMessageId']
                c.execute('''UPDATE settings SET message_id=? WHERE user_id=?''', (message_id, user_id))
        api_name = str(call.data)
        c.execute('''UPDATE settings SET api_name=? WHERE user_id=?''', (api_name, user_id))
        await bot.send_message( call.message.chat.id,api_name+' is active')
    elif call.data in models:
        model = str(call.data)
        await bot.send_message( call.message.chat.id,model+' is active')
        c.execute('''UPDATE settings SET model=? WHERE user_id=?''', (model, user_id))
    conn.commit()
#hello or start command handler
@bot.message_handler(commands=['hello', 'start'])
async def start_handler(message):
    # Insert the user into the settings table if they don't exist yet
    c.execute('''INSERT OR IGNORE INTO settings (user_id, api_name, model,message_id)
                 VALUES (?, ?, ?, ?)''', (message.chat.id, 'deepai', 'ChatGPT',''))
    conn.commit()
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
    c.execute('''SELECT * FROM settings WHERE user_id=?''', (message.from_user.id,))
    row = c.fetchone()
    user_id, api_name, model, message_id = row
    if api_name != 'quora':
        await bot.send_message(message.chat.id,'changebot command only available for poe')
        return
    _models = telebot.types.InlineKeyboardMarkup() 
    #making buttons with the model dictionary 
    for i in models:
        _models.add(telebot.types.InlineKeyboardButton(i+'(Codename:'+models[i]+')', callback_data=i))
    await bot.send_message(message.chat.id,'Currently '+model+' is active'+\
                     ' (gpt-4 and claude-v1.2 requires a paid subscription)', reply_markup=_models)
#changeprovider command handler
@bot.message_handler(commands=['changeprovider'])
async def changeprovider_handler(message):
    _providers = telebot.types.InlineKeyboardMarkup()
    for i in providers:
        _providers.add(telebot.types.InlineKeyboardButton(i, callback_data=i))
    await bot.send_message(message.chat.id,'Currently '+api_name+' is active', reply_markup=_providers)
#Messages other than commands handled 
@bot.message_handler(content_types='text')
async def reply_handler(call):
    c.execute('''SELECT api_name, model FROM settings WHERE user_id=?''', (call.from_user.id,))
    row = c.fetchone()
    if row:
        api_name, model = row
    else:
        api_name, model = 'deepai', 'ChatGPT'
    
    await bot.send_chat_action(call.chat.id, "typing")
    sent = await bot.send_message(call.chat.id, "Please wait while i think")
    message_id = sent.message_id
    try:
        text = await stream(call,model,api_name)
    except RuntimeError as error: 
        if " ".join(str(error).split()[:3]) == "Daily limit reached":
            text = "Daily Limit reached for current bot. please use another bot or another provider"
        else:
            text = str(error)
    if api_name == 'Stable Diffusion(generate image)':
        await bot.send_photo(chat_id=call.chat.id, photo=open(text, 'rb'))
        await bot.edit_message_text(chat_id=call.chat.id, message_id=message_id, text="Image Generated")      
    else:
        c.execute('''INSERT INTO history (user_id, role, content)
                 VALUES (?, ?, ?)''', (call.chat.id, 'user', call.text))
        c.execute('''INSERT INTO history (user_id, role, content)
                 VALUES (?, ?, ?)''', (call.chat.id, 'assistant', text))
        conn.commit()
        await bot.delete_message(chat_id=call.chat.id, message_id=message_id)
        await bot.send_message(call.chat.id,text)
#messages with audio
@bot.message_handler(content_types=['voice', 'audio'])
async def audio_handler(call):
    c.execute('''SELECT api_name, model FROM settings WHERE user_id=?''', (call.from_user.id,))
    row = c.fetchone()
    if row:
        api_name, model = row
    else:
        api_name, model = 'deepai', 'ChatGPT'
    audio_file_path = await download_audio_file_from_message(call)
    print(audio_file_path)
    transcribed_audio = await bn.transcribe_audio(audio_file_path)
    sent = await bot.send_message(call.chat.id,'Transcribed audio:' + transcribed_audio)
    await reply_handler(sent)
#Messages with image 
@bot.message_handler(content_types='photo')
async def image_handler(call): 
        file_id = call.photo[-1].file_id
        file_info = await bot.get_file(file_id)
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

