from aiogram.types import ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ParseMode,File
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from bot import botfn,botdb,botocr,botmedia
import yaml
import yaml
import datetime
import os
import asyncio
import random
import logging

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
HG_TOKEN = os.getenv('HG_TOKEN')
HG_img2text = os.getenv('HG_img2text')
language = os.getenv('LANG')
if os.path.exists('lang.yml'):
    with open("lang.yml", 'r', encoding='utf8') as f:
        lang = yaml.safe_load(f)
else:
    print('lang.yml does not exist.')
    exit
language = os.getenv('LANG')
if os.path.exists('lang.yml'):
    with open("lang.yml", 'r', encoding='utf8') as f:
        lang = yaml.safe_load(f)
else:
    print('lang.yml does not exist.')
    exit
instruction_file = 'instructions.txt'
messages = [
    "Please wait...","Hang on a sec...","Just a moment...","Processing your request...",
    "Almost done...","Working on it...","One moment please...","Patience is a virtue...",
    "Hold tight...","Be right back...","We're on it...","Doing our thing...","Sit tight...",
    "Almost there...","Just a little longer...","Processing...","Stay put...",
]
logging.basicConfig(level=logging.INFO)
bn = botfn.botfn(lang)
logging.basicConfig(level=logging.INFO)
bn = botfn.botfn(lang)
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
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot,storage=storage)
#bot = AsyncTeleBot(BOT_TOKEN,state_storage=StateMemoryStorage())
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot,storage=storage)
#bot = AsyncTeleBot(BOT_TOKEN,state_storage=StateMemoryStorage())

class MyStates(StatesGroup):
    SELECT_PROMPT = State() 
    SELECT_STYLE = State()
    SELECT_RATIO = State()
    SELECT_LANG = State()
    SELECT_LANG = State()

async def send_with_waiting_message(chat_id):
    waiting_message = random.choice(messages)
    sent = await bot.send_message(chat_id=chat_id,
                                    text="⏳ "+waiting_message)
    sent = await bot.send_message(chat_id=chat_id,
                                    text="⏳ "+waiting_message)
    message_id = sent.message_id
    chat_action_task = asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    await asyncio.sleep(3) 
    await bot.delete_message(chat_id=chat_id, message_id=message_id)

@dp.message_handler(commands=['start', 'hello'])
async def start_handler(call: types.Message):
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    lan = db.get_settings(call.chat.id)
    if lan == None:
        lan = 'en'
        db.insert_settings(call.chat.id, lan)
    language = lang['languages'][lan]
    welcome = f"""First, you will introduce yourself, you will welcome the user and last you will tell the user to use the /help command if help is needed
you will need to explain to the user in a specific language, completely translated.
the language to explain as a native is: {language}."""
    search_results = "No search query is needed for a response"
    text = await bn.generate_response(instruction,search_results,history={},prompt=welcome)
    await bot.send_message(call.chat.id,text=text)

@dp.message_handler(commands=['help'])
async def help_handler(call: types.Message):
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    language = lang['languages'][db.get_settings(call.from_user.id)]
    help = f"""First, you will introduce yourself, you will welcome the user and talk about:
    Commands:
    /start : starts the bot\n\
    /lang : change language\n\
    /img : Generate image using imaginepy\n\
    /help : list all commands
    Some features:
🎨 User can make the bot generate image generation with /img
🎤 User can send voice messages instead of text.
📖 User can send documents or links to analyze them with the bot!
🖼️ User can send photos to extract the text from them.
you will be pleasant and attentive, you will not miss any detail, remember to use line breaks. if the user asks about something about the bot, you will answer with pleasure
all the previous information you will need to explain to the user in a specific language, completely translated.
the language to explain as a native is: {language}."""
    search_results = "No search query is needed for a response"
    text = await bn.generate_response(instruction,search_results,history={},prompt=help)
    await bot.send_message(call.chat.id,text=text)

@dp.message_handler(commands=['lang'])
async def lang_handler(call: types.Message):
    markup = await bn.generate_keyboard('lang')
    await bot.send_message(call.chat.id,
        "Please select a language from the available languages:", reply_markup=markup
    )
    await MyStates.SELECT_LANG.set()

@dp.message_handler(state=MyStates.SELECT_LANG)
async def select_lang(call: types.Message, state: FSMContext):
    lang_code = call.text[-3:-1]
    if lang_code in lang['available_lang']:
        db.update_settings(call.chat.id,lang_code)
        markup = ReplyKeyboardRemove()  
        await call.answer(f'Language set to {lang["languages"][lang_code]}',reply_markup=markup)
        await state.finish()
    else:
        await lang_handler(call)

@dp.message_handler(commands=['img'])
async def img_handler(call: types.Message):
    await bot.send_message(call.chat.id,text="Let's imagine something. Enter your prompt")
    await MyStates.SELECT_PROMPT.set()

@dp.message_handler(state=MyStates.SELECT_PROMPT)
async def select_style(call: types.Message, state: FSMContext):
    async with state.proxy() as data:
@dp.message_handler(state=MyStates.SELECT_PROMPT)
async def select_style(call: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['prompt'] = call.text
    markup = await bn.generate_keyboard('style')
    await bot.send_message(call.chat.id,
        "Please select a style:", reply_markup=markup
    )
    await MyStates.next()
    await MyStates.next()
    
@dp.message_handler(state=MyStates.SELECT_STYLE)
async def select_ratio(call: types.Message, state: FSMContext):
@dp.message_handler(state=MyStates.SELECT_STYLE)
async def select_ratio(call: types.Message, state: FSMContext):
    if call.text in bn._STYLE_OPTIONS.keys():
        async with state.proxy() as data:
        async with state.proxy() as data:
            data['style'] = bn._STYLE_OPTIONS[call.text]
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(call.chat.id,
            "Please select a ratio:", reply_markup=markup
        )
    else:
        markup = await bn.generate_keyboard('style')
        await bot.send_message(call.chat.id,
            "Select a valid style", reply_markup=markup
        )
        await MyStates.SELECT_STYLE.set()
        await MyStates.SELECT_STYLE.set()
        return
    await MyStates.SELECT_RATIO.set()
    await MyStates.SELECT_RATIO.set()

@dp.message_handler(state=MyStates.SELECT_RATIO)
async def generate_image(call: types.Message, state: FSMContext):
@dp.message_handler(state=MyStates.SELECT_RATIO)
async def generate_image(call: types.Message, state: FSMContext):
    if call.text in bn._RATIO_OPTIONS.keys():
        chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
        async with state.get_data() as data:
        async with state.get_data() as data:
            prompt = data['prompt']
            style = data['style']
        ratio = bn._RATIO_OPTIONS[call.text]
        text_task = asyncio.create_task(bm.generate_image(image_prompt=prompt,
                          style_value=style ,
                          ratio_value=ratio,negative=''))
        filename = await text_task
        await call.reply_photo(photo=open(filename,'rb')) 
        await call.reply_photo(photo=open(filename,'rb')) 
        markup = ReplyKeyboardRemove()  
        await bot.send_message(call.chat.id,'Image Generated',reply_markup=markup)
        os.remove(filename)
    else:
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(call.chat.id,
            "Select a valid ratio", reply_markup=markup
        )
        await MyStates.SELECT_RATIO.set()
        await MyStates.SELECT_RATIO.set()
        return
    await state.finish()
    await state.finish()

@dp.message_handler(content_types=['text'])
async def chat(call:types.Message):
@dp.message_handler(content_types=['text'])
async def chat(call:types.Message):
    global instruction
    language = lang['languages'][db.get_settings(call.from_user.id)]
    language = lang['languages'][db.get_settings(call.from_user.id)]
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    rows = db.get_history(call.from_user.id)[-9:]
    history = []
    prompt = call.text
    for row in rows:
        role, content = row
        history.append({"role": role, "content": content})
    instruction += f'\nYou will need to reply to the user in {language} as a native. Completely translated.'
    instruction += f'\nYou will need to reply to the user in {language} as a native. Completely translated.'
    search_results = await bn.search_ddg(call.text)
    if not search_results:
        search_results = 'Search feature is currently disabled so you have no realtime information'
    web_text = await bn.extract_text_from_website(call.text)
    if web_text is not None:
        prompt = web_text
    yt_transcript = await bn.get_yt_transcript(call.text)
    if yt_transcript is not None:
        prompt = yt_transcript
    text = await bn.generate_response(instruction,search_results,history,prompt)
    db.insert_history(call.from_user.id, 'user', call.text)
    db.insert_history(call.from_user.id, 'assistant', text)
    message_task = asyncio.create_task(bot.send_message(call.chat.id,text))
    message = await message_task

@dp.message_handler(content_types=['voice', 'audio', 'photo', 'document'])
async def imageaudio_handler(call: types.Message): 
@dp.message_handler(content_types=['voice', 'audio', 'photo', 'document'])
async def imageaudio_handler(call: types.Message): 
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    global instruction
    language = lang['languages'][db.get_settings(call.from_user.id)]
    instruction += f'\nYou will need to reply to the user in {language} as a native. Completely translated.'
    language = lang['languages'][db.get_settings(call.from_user.id)]
    instruction += f'\nYou will need to reply to the user in {language} as a native. Completely translated.'
    rows = db.get_history(call.from_user.id)[-10:]
    history = []
    for row in rows:
        role, content = row
        history.append({"role": role, "content": content})
    #for attachment in call.attachments:
    if call.content_type == 'photo':
        file_info = await bot.get_file(call.photo[-1].file_id)
        image_url = f"https://api.telegram.org/file/bot{bot._token}/{file_info.file_path}"
        ocr_text = ocr.process_image(image_url)
        if HG_TOKEN and ocr_text:
            text = await bm.generate_imagecaption(image_url,HG_TOKEN)
            await call.reply(text)
            prompt = 'System: The following is a image context provided by an image to text model.\
                 Generate a caption for the image context provided by an image-to-text model and respond appropriately.\n'\
                  + text + \
                  '\nSystem: The following is a image context generated by an OCR model\
                     If the text in the image is readable, please incorporate it into your response. If the text is gibberish or unreadable, please disregard it.\n'\
                  + ocr_text  
            text += ocr_text
        elif HG_TOKEN:
            text = await bm.generate_imagecaption(image_url,HG_TOKEN)
            ocr_text = ''
            await call.reply(text)
            prompt = 'System: The following is a image context provided by an image to text model.\
                 Generate a caption for the image context provided by an image-to-text model and respond appropriately.\n'\
                  + text
        elif ocr_text:
            text = ocr_text
            prompt = '\nSystem: The following is a image context generated by an OCR model\
                     If the text in the image is readable, please incorporate it into your response. If the text is gibberish or unreadable, please disregard it.\n'\
                  + ocr_text
        else:
            text = ocr_text = ''
            prompt = '\nSystem: The image to text model could not read anything from the image the user sent. '
        prompt += '\nGenerate a response based on the context of an image, even if the image itself is not visible.'
    elif call.content_type == 'document':
        file_path = await bm.download_file(call)
        text = await bm.read_document(file_path)
        prompt = f'\nSystem: Generate a response based on the contents of the file provided by the user. If there is no text present in the file, respond with "I couldn\'t read that."\n{text}'
        search_results = ''
        os.remove(file_path)
    elif call.content_type == 'audio' or 'voice':
        audio_file_path = await bm.download_file(call)
        text = await bm.transcribe_audio(audio_file_path)
        sent = await call.reply('Transcribed audio:' + text)
        prompt = '\nSystem: The following is a transcription of the user\'s command generated by a voice-to-text model. Review it and generate appropriate response. If there are any transcription errors, please provide the appropriate response. If the text is empty or garbled, reply with "I didn\'t understand that."\n'+text
        os.remove(audio_file_path)
    else:
        return
    if text != '' and call.content_type != 'document':
        search_results = await bn.search_ddg(text)
    if not search_results:
        search_results = 'Search feature is currently disabled so you have no realtime information'
    response = await bn.generate_response(instruction,search_results,history,prompt)
    await call.reply(response)
    db.insert_history(call.chat.id, 'user', text)
    db.insert_history(call.chat.id, 'assistant', response)

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
async def main():
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
db.close_connection()