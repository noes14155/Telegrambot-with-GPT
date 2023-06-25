from aiogram.types import ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode,File
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv
from bot import botfn,botdb,botocr,botmedia
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
default_language = os.getenv('DEFAULT_LANGUAGE')

plugin_lang = ''

if os.path.exists('language_files\languages.yml'):
    with open("language_files\languages.yml", 'r', encoding='utf8') as f:
        available_lang = yaml.safe_load(f)
else:
    print('languages.yml does not exist')
    exit

if BOT_TOKEN == "":
    print('No BOT-TOKEN found! Add it in your env file')
exit

logging.basicConfig(level=logging.INFO)
bn = botfn.botfn(available_lang)
bm = botmedia.botmedia(HG_img2text)
db = botdb.Database('chatbot.db')
ocr = botocr.OCR(config=" --psm 3 --oem 3 -l script/Devanagari")
db.create_tables()
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot,storage=storage)

def user_language(user_id=None):
    if user_id:
        lang = db.get_settings(user_id)
    else:
        lang=None
    if lang:
        language = lang
    else:
        language = default_language
        db.insert_settings(user_id, language)
    language_file_path = f'language_files/{language}.yml'
    if os.path.exists(language_file_path):
        with open(language_file_path, 'r', encoding='utf-8') as file:
            bot_messages = yaml.safe_load(file)
    else:
        print(f'{language_file_path} does not exist, Using English')
        language = 'en'
        with open(f'language_files/en.yml', 'r', encoding='utf-8') as file:
            bot_messages = yaml.safe_load(file)
    db.update_settings(user_id, language)
    bot_messages['bot_prompt'] += f"\n\nIt's currently {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ###########################
    global plugin_lang
    plugin_lang = bot_messages
    ###########################
    return bot_messages

user_language() #Temporary Solution
PLUGINS = False
plugins_dict = plugin_lang['plugins_dict']
plugins_string = ''
for plugin in plugins_dict:
    plugins_string += f"\n{plugin}: {plugins_dict[plugin]}"
PLUGIN_PROMPT = plugin_lang['PLUGIN_PROMPT'] + plugins_string

class MyStates(StatesGroup):
    SELECT_PROMPT = State() 
    SELECT_STYLE = State()
    SELECT_RATIO = State()
    SELECT_LANG = State()

async def send_with_waiting_message(chat_id):
    bot_messages = user_language(chat_id)
    waiting_message = random.choice(bot_messages['waiting_messages'])
    sent = await bot.send_message(chat_id=chat_id, text="⏳ " + waiting_message)
    chat_action_task = asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    await asyncio.sleep(3) 
    await bot.delete_message(chat_id=chat_id, message_id=sent.message_id)  

@dp.message_handler(commands=['start', 'hello'])
async def start_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    lang = db.get_settings(call.from_id)
    language = available_lang['languages'][lang]
    welcome = bot_messages["start"] + f"{language}."
    search_results = "No search query is needed for a response"
    text = await bn.generate_response(bot_messages['bot_prompt'],'','',history={},prompt=welcome)
    await bot.send_message(call.chat.id,text=text)
    await set_commands(call.from_user.id)

@dp.message_handler(commands=['clear'])
async def clear_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    db.delete_user_history(call.chat.id)
    await bot.send_message(call.chat.id, '🧹 ' + bot_messages['history_cleared'])

@dp.message_handler(commands=['help'])
async def help_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    language = available_lang['languages'].get(db.get_settings(call.from_user.id), available_lang['languages']['en'])
    help = bot_messages['help'] + f'{language}.'
    search_results = "No search query is needed for a response"
    text = await bn.generate_response(bot_messages['bot_prompt'],'','',history={},prompt=help)
    await bot.send_message(call.chat.id,text=text)

@dp.message_handler(commands=['lang'])
async def lang_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    markup = await bn.generate_keyboard('lang')
    await bot.send_message(call.chat.id, bot_messages['lang_select'], reply_markup=markup)
    await MyStates.SELECT_LANG.set()

@dp.message_handler(state=MyStates.SELECT_LANG)
async def select_lang(call: types.Message, state: FSMContext):
    bot_messages = user_language(call.from_user.id)
    lang_code = call.text[-3:-1]
    if lang_code in available_lang['available_lang']:
        db.update_settings(call.chat.id,lang_code)
        markup = ReplyKeyboardRemove()  
        await call.answer(bot_messages['lang_selected'] + available_lang["languages"][lang_code], reply_markup=markup)
        await state.finish()
        await set_commands(call.from_user.id)
    else:
        await lang_handler(call)

@dp.message_handler(commands=['img'])
async def img_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    await bot.send_message(call.chat.id,text=bot_messages['img_prompt'])
    await MyStates.SELECT_PROMPT.set()

@dp.message_handler(state=MyStates.SELECT_PROMPT)
async def select_style(call: types.Message, state: FSMContext):
    bot_messages = user_language(call.from_user.id)
    async with state.proxy() as data:
        data['prompt'] = call.text
    markup = await bn.generate_keyboard('style')
    await bot.send_message(call.chat.id, bot_messages['img_style'], reply_markup=markup)
    await MyStates.next()
    
@dp.message_handler(state=MyStates.SELECT_STYLE)
async def select_ratio(call: types.Message, state: FSMContext):
    bot_messages = user_language(call.from_user.id)
    if call.text in bn._STYLE_OPTIONS.keys():
        async with state.proxy() as data:
            data['style'] = bn._STYLE_OPTIONS[call.text]
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(call.chat.id, bot_messages['img_ratio'], reply_markup=markup)
    else:
        markup = await bn.generate_keyboard('style')
        await bot.send_message(call.chat.id, bot_messages['img_style'], reply_markup=markup)
        await MyStates.SELECT_STYLE.set()
        return
    await MyStates.SELECT_RATIO.set()

@dp.message_handler(state=MyStates.SELECT_RATIO)
async def generate_image(call: types.Message, state: FSMContext):
    bot_messages = user_language(call.from_user.id)
    if call.text in bn._RATIO_OPTIONS.keys():
        chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
        data = await state.get_data()
        prompt = data['prompt']
        style = data['style']
        ratio = bn._RATIO_OPTIONS[call.text]
        await bot.send_chat_action(call.chat.id,"upload_photo")
        text_task = asyncio.create_task(bm.generate_image(image_prompt=prompt,
                          style_value=style ,
                          ratio_value=ratio,negative=''))
        filename = await text_task
        if filename:
            await bot.send_photo(call.chat.id,photo=open(filename,'rb'))
            markup = ReplyKeyboardRemove()  
            await bot.send_message(call.chat.id, bot_messages['img_generated'], reply_markup=markup)
            os.remove(filename)
        else:
            markup = ReplyKeyboardRemove()
            await bot.send_message(call.chat.id, bot_messages['img_error'], reply_markup=markup)
    else:
        markup = await bn.generate_keyboard('ratio')
        await bot.send_message(call.chat.id, bot_messages['img_ratio'], reply_markup=markup)
        await MyStates.SELECT_RATIO.set()
    await state.finish()

@dp.message_handler(content_types=['text'])
async def chat(call:types.Message):
    bot_messages = user_language(call.from_user.id)
    language = available_lang['languages'].get(db.get_settings(call.from_user.id), available_lang['languages']['en'])
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    rows = db.get_history(call.from_user.id)[-5:]
    history = []
    prompt = call.text
    for row in rows:
        role, content = row
        history.append({"role": role, "content": content})
    bot_messages['bot_prompt'] += bot_messages['translator_prompt']
    # search_results = await bn.search_ddg(call.text)
    # if not search_results:
    #     search_results = 'Search feature is currently disabled so you have no realtime information'
    web_text = await bn.extract_text_from_website(call.text)
    if web_text is not None:
        prompt = web_text
    yt_transcript = await bn.get_yt_transcript(call.text)
    if yt_transcript is not None:
        prompt = yt_transcript
    EXTRA_PROMPT = bot_messages['EXTRA_PROMPT']
    text = await bn.generate_response(PLUGIN_PROMPT,'plugins',EXTRA_PROMPT,{},prompt)
    result, plugin_name = await bn.generate_query(text,plugins_dict)
    if result is None and plugin_name is None:
        text = await bn.generate_response(bot_messages['bot_prompt'],'','',history,prompt)
    else:
        text = await bn.generate_response(bot_messages['bot_prompt'],plugin_name,result,history,prompt)
    db.insert_history(call.from_user.id, 'user', call.text)
    db.insert_history(call.from_user.id, 'assistant', text)
    await bot.send_message(call.chat.id,text)

@dp.message_handler(content_types=['voice', 'audio', 'photo', 'document'])
async def imageaudio_handler(call: types.Message):
    bot_messages = user_language(call.from_user.id)
    chat_action_task = asyncio.create_task(send_with_waiting_message(call.chat.id))
    bot_messages['bot_prompt'] += bot_messages['translator_prompt']
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
            prompt = bot_messages['image_description_prompt']\
                  + text + \
                  bot_messages['image_context_prompt']\
                  + ocr_text  
            text += ocr_text
        elif HG_TOKEN:
            text = await bm.generate_imagecaption(image_url,HG_TOKEN)
            ocr_text = ''
            await call.reply(text)
            prompt = bot_messages['image_description_prompt'] + text
        elif ocr_text:
            text = ocr_text
            prompt = bot_messages['image_context_prompt'] + ocr_text
        else:
            text = ocr_text = ''
            prompt = bot_messages['image_couldnt_read_prompt']
        prompt += bot_messages['image_output_prompt']
    elif call.content_type == 'document':
        file_path = await bm.download_file(call)
        text = await bm.read_document(file_path)
        prompt = bot_messages['document_prompt'] + text
        search_results = ''
        os.remove(file_path)
    elif call.content_type == 'audio' or 'voice':
        audio_file_path = await bm.download_file(call)
        text = await bm.transcribe_audio(audio_file_path)
        sent = await call.reply(bot_messages['voice_transcribed'] + text)
        prompt = bot_messages['voice_prompt'] + text
        os.remove(audio_file_path)
    else:
        return
    if text != '' and call.content_type != 'document':
        search_results = await bn.search_ddg(text)
    if not search_results:
        search_results = 'Search feature is currently disabled so you have no realtime information'
    response = await bn.generate_response(bot_messages['bot_prompt'],'','',history,prompt)
    await call.reply(response)
    db.insert_history(call.chat.id, 'user', text)
    db.insert_history(call.chat.id, 'assistant', response)

async def set_commands(user_id):
    bot_messages = user_language(user_id)
    commands = [
    types.BotCommand(command="/hello", description="🌟 " + bot_messages["hello_description"]),
    types.BotCommand(command="/img", description="🎨 " + bot_messages["img_description"]),
    types.BotCommand(command="/lang", description="🌐 " + bot_messages["lang_description"]),
    types.BotCommand(command='/clear', description="🧹 " + bot_messages["clear_description"]),
    types.BotCommand(command="/help", description="ℹ️ " + bot_messages["help_description"])
    ]
    await bot.delete_my_commands()
    await bot.set_my_commands(commands)

async def main():
    await asyncio.gather(set_commands(None),dp.start_polling())

if __name__ == '__main__':
    asyncio.run(main())

db.close_connection()