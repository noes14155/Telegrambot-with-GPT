from telebot.types import ReplyKeyboardRemove
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_handler_backends import State, StatesGroup
from telebot.asyncio_storage import StateMemoryStorage
from telebot import asyncio_filters
from dotenv import load_dotenv
from bot import botfn,botdb,botocr,botmedia
import datetime
import os
import asyncio
import random

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
HG_TOKEN = os.getenv('HG_TOKEN')
HG_img2text = os.getenv('HG_img2text')

instruction_file = 'instructions.txt'
messages = [
    "Please wait...","Hang on a sec...","Just a moment...","Processing your request...",
    "Almost done...","Working on it...","One moment please...","Patience is a virtue...",
    "Hold tight...","Be right back...","We're on it...","Doing our thing...","Sit tight...",
    "Almost there...","Just a little longer...","Processing...","Stay put...",
]

bn = botfn.botfn()
bm = botmedia.botmedia(HG_img2text)
db = botdb.Database('chatbot.db')
ocr = botocr.OCR(config=" --psm 3 --oem 3 -l script/Devanagari")
db.create_tables()
if os.path.exists(instruction_file):
    with open(instruction_file, 'r') as file:
        instruction = file.read()
        instruction += f"\n\nIt's currently {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
else:
    print(f'{instruction_file} does not exist')
    instruction = ''

if BOT_TOKEN == "":
   print('No BOT-TOKEN found! Add it in your env file')
   exit
bot = AsyncTeleBot(BOT_TOKEN,state_storage=StateMemoryStorage())
class MyStates(StatesGroup):
    SELECT_PROMPT = State() 
    SELECT_STYLE = State()
    SELECT_RATIO = State()

async def send_with_waiting_message(chat_id):
    waiting_message = random.choice(messages)
    sent = await bot.send_animation(chat_id=chat_id,
                                    animation="https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif",
                                    caption=waiting_message)
    message_id = sent.message_id
    chat_action_task = asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    await asyncio.sleep(3) 
    await bot.delete_message(chat_id=chat_id, message_id=message_id)

@bot.message_handler(commands=['start', 'hello'])
async def start_handler(call):
    db.insert_settings(call.chat.id, 'AI Assist', 'ChatGPT')
    await bot.send_message(call.chat.id,text="Hello, Welcome to GPT4free.\n"\
                     "\nUse command /changeprovider or /changebot to change to a different bot\n\
                        Ask me anything I am here to help you.")

@bot.message_handler(commands=['help'])
async def help_handler(call):
    await bot.send_message(call.chat.id,text="  /start : starts the bot\n\
    /img : Generate image using imaginepy\n\
    /help : list all commands")

@bot.message_handler(commands=['img'])
async def img_handler(call):
    await bot.send_message(call.chat.id,text="Let's imagine something. Enter your prompt")
    await bot.set_state(call.from_user.id, MyStates.SELECT_PROMPT, call.chat.id)

@bot.message_handler(state=MyStates.SELECT_PROMPT)
async def select_style(call):
    async with bot.retrieve_data(call.from_user.id, call.chat.id) as data:
        data['prompt'] = call.text
    markup = await bn.generate_keyboard('style')
    await bot.send_message(
        call.chat.id,
        "Please select a style:", reply_markup=markup
    )
    await bot.set_state(call.from_user.id, MyStates.SELECT_STYLE, call.chat.id)
    
@bot.message_handler(state=MyStates.SELECT_STYLE)
async def select_ratio(call):
    if call.text in bn._STYLE_OPTIONS.keys():
        async with bot.retrieve_data(call.from_user.id, call.chat.id) as data:
            data['style'] = bn._STYLE_OPTIONS[call.text]
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(
            call.chat.id,
            "Please select a ratio:", reply_markup=markup
        )
    else:
        markup = await bn.generate_keyboard('style')
        await bot.send_message(
            call.chat.id,
            "Select a valid style", reply_markup=markup
        )
        await bot.set_state(call.from_user.id, MyStates.SELECT_STYLE, call.chat.id)
        return
    await bot.set_state(call.from_user.id, MyStates.SELECT_RATIO, call.chat.id)

@bot.message_handler(state=MyStates.SELECT_RATIO)
async def generate_image(call):
    if call.text in bn._RATIO_OPTIONS.keys():
        chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
        async with bot.retrieve_data(call.from_user.id, call.chat.id) as data:
            prompt = data['prompt']
            style = data['style']
        ratio = bn._RATIO_OPTIONS[call.text]
        text_task = asyncio.create_task(bm.generate_image(image_prompt=prompt,
                          style_value=style ,
                          ratio_value=ratio,negative=''))
        filename = await text_task
        await bot.send_photo(call.chat.id,photo=open(filename,'rb')) 
        markup = ReplyKeyboardRemove()  
        await bot.send_message(call.from_user.id,'Image Generated',reply_markup=markup)
        os.remove(filename)
    else:
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(
            call.chat.id,
            "Select a valid ratio", reply_markup=markup
        )
        await bot.set_state(call.from_user.id, MyStates.SELECT_RATIO, call.chat.id)
        return
    await bot.delete_state(call.from_user.id, call.chat.id)

@bot.message_handler(content_types='text')
async def chat(call):
    global instruction
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    rows = db.get_history(call.from_user.id)[-9:]
    history = []
    prompt = call.text
    for row in rows:
        role, content = row
        history.append({"role": role, "content": content})
    search_results = await bn.search_ddg(call.text)
    if not search_results:
        search_results = 'Search feature is currently disabled so you have no realtime information'
    web_text = await bn.extract_text_from_website(call.text)
    if web_text is not None:
        prompt = web_text
    yt_transcript = await bn.get_yt_transcript(prompt)
    if yt_transcript is not None:
        chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
        prompt = yt_transcript
    text = await bn.generate_response(instruction,search_results,history,prompt)
    db.insert_history(call.from_user.id, 'user', call.text)
    db.insert_history(call.from_user.id, 'assistant', text)
    message_task = asyncio.create_task(bot.send_message(call.chat.id,text))
    message = await message_task

@bot.message_handler(content_types=['voice', 'audio', 'photo', 'document'])
async def imageaudio_handler(call): 
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    global instruction
    rows = db.get_history(call.from_user.id)[-10:]
    history = []
    for row in rows:
        role, content = row
        history.append({"role": role, "content": content})
    #for attachment in call.attachments:
    if call.content_type == 'photo':
        file_info = await bot.get_file(call.photo[-1].file_id)
        image_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
        ocr_text = ocr.process_image(image_url)
        if HG_TOKEN and ocr_text:
            text = await bm.generate_imagecaption(image_url,HG_TOKEN)
            await bot.send_message(call.chat.id,text)
            prompt = 'System: This is a image context provided by an image to text model. Generate a caption with an appropriate response.'\
                  + text + \
                  '\nSystem: This is a image context provided by a OCR model which is not stable. If it\'s gibberish leave it out of your answer if its readable answer accordingly'\
                  + ocr_text  
            text += ocr_text
        elif HG_TOKEN:
            text = await bm.generate_imagecaption(image_url,HG_TOKEN)
            ocr_text = ''
            await bot.send_message(call.chat.id,text)
            prompt = 'System: This is a image context provided by an image to text model. Generate a caption with an appropriate response.'\
                  + text
        elif ocr_text:
            text = ocr_text
            prompt = '\nSystem: This is a image context provided by a OCR model which is not stable. If it\'s gibberish leave it out of your answer if its readable answer accordingly'\
                  + ocr_text
        else:
            text = ocr_text = ''
            prompt = '\nSystem: The image to text model could not read anything from the image the user sent. '
    elif call.content_type == 'document':
        file_path = await bm.download_file_from_message(bot,call)
        text = await bm.read_document(file_path)
        prompt = f"\nSystem: Summarize the following text into bullet points. And provide an appropriate response. If there is no text present respond with i couldn't read that.\n{text}"
        search_results = ''
        os.remove(file_path)
    elif call.content_type == 'audio' or 'voice':
        audio_file_path = await bm.download_file_from_message(bot,call)
        text = await bm.transcribe_audio(audio_file_path)
        sent = await bot.send_message(call.chat.id,'Transcribed audio:' + text)
        prompt = '\nSystem: The following is a transcription of the user\'s command provided by an voice to text model. May contain transcription errors reply accordingly and if the text is empty of garbled reply with "I didn\'t understand that\n'+text
        os.remove(audio_file_path)
    else:
        return
    if text != '' and call.content_type != 'document':
        search_results = await bn.search_ddg(text)
    if not search_results:
        search_results = 'Search feature is currently disabled so you have no realtime information'
    response = await bn.generate_response(instruction,search_results,history,prompt)
    await bot.send_message(call.chat.id,response)
    db.insert_history(call.chat.id, 'user', text)
    db.insert_history(call.chat.id, 'assistant', response)

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
asyncio.run(bot.polling())
db.close_connection()