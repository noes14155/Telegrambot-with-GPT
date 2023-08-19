import asyncio
import logging
import os
import random
from updater import SelfUpdating
from io import BytesIO
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatType
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from functools import wraps

import bot_service
from replit_detector import ReplitFlaskApp

service = bot_service.BotService()
updater = SelfUpdating('noes14155/Telegrambot-with-GPT4free')
storage = MemoryStorage()
bot = Bot(token=service.BOT_TOKEN)
owner_id = service.BOT_OWNER_ID
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
dm_enabled = True

class MyStates(StatesGroup):
    SELECT_PROMPT = State()
    SELECT_STYLE = State()
    SELECT_RATIO = State()
    SELECT_LANG = State()
    SELECT_PERSONA = State()
    SELECT_MODEL = State()
    SELECT_SIZE = State()

def owner_only(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        if update.message.from_user.username != owner_id:
            await update.message.reply("Only the bot owner can use this command!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

async def create_waiting_message(chat_id):
    bot_messages = service.lm.local_messages(user_id=chat_id)
    waiting_message = random.choice(bot_messages["waiting_messages"])
    sent = await bot.send_message(chat_id=chat_id, text="⏳ " + waiting_message)
    asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    return sent.message_id


async def delete_waiting_message(chat_id, waiting_id):
    await bot.delete_message(chat_id=chat_id, message_id=waiting_id)


@dp.message_handler(commands=["start", "hello"])
async def start_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.start(user_id=call.from_user.id)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await bot.send_message(chat_id=call.chat.id, text=response)
    await set_commands(user_id=call.from_user.id)


@dp.message_handler(commands=["clear"])
async def clear_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.clear(user_id=call.from_user.id)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await bot.send_message(chat_id=call.chat.id, text=response)


@dp.message_handler(commands=["help"])
async def help_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.help(user_id=call.from_user.id)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await bot.send_message(chat_id=call.chat.id, text=response)

@dp.message_handler(commands=["changepersona"])
async def persona_handler(call: types.Message):
    response, markup = await service.changepersona()
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await MyStates.SELECT_PERSONA.set()

@dp.message_handler(state=MyStates.SELECT_PERSONA)
async def select_persona_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_persona(user_id=call.from_user.id,user_message=call.text)
    if response and markup:
        await state.finish()
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    else:
        await persona_handler(call)


@dp.message_handler(commands=["lang"])
async def lang_handler(call: types.Message):
    response, markup = await service.lang(user_id=call.from_user.id)
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await MyStates.SELECT_LANG.set()


@dp.message_handler(state=MyStates.SELECT_LANG)
async def select_lang_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_lang(
        user_id=call.from_user.id, user_message=call.text[-3:-1]
    )
    if response and markup:
        await call.answer(text=response, reply_markup=markup)
        await state.finish()
        await set_commands(user_id=call.from_user.id)
    else:
        await lang_handler(call)

@dp.message_handler(commands=["changemodel"])
async def model_handler(call: types.Message):
    response, markup = await service.changemodel()
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await MyStates.SELECT_MODEL.set()

@dp.message_handler(state=MyStates.SELECT_MODEL)
async def select_model_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_model(user_id=call.from_user.id,user_message=call.text)
    if response and markup:
        await state.finish()
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    else:
        await model_handler(call)

@dp.message_handler(commands=["img","dalle"])
async def img_handler(call: types.Message, state: FSMContext):
    await state.update_data(command=call.text)
    response = await service.img(user_id=call.from_user.id)
    await bot.send_message(call.chat.id, text=response)
    await MyStates.SELECT_PROMPT.set()


@dp.message_handler(state=MyStates.SELECT_PROMPT)
async def select_prompt_handler(call: types.Message, state: FSMContext):
    filename, markup = await service.select_prompt(
        user_id=call.from_user.id, user_message=call.text, state=state
    )
    if markup == None:
        waiting_id = await create_waiting_message(chat_id=call.chat.id)
        await bot.send_chat_action(chat_id=call.chat.id, action="upload_photo")
        photo = open(filename, "rb")
        await bot.send_photo(chat_id=call.chat.id, photo=photo)
        await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
        os.remove(filename)
        await state.finish()
    else:
        response = 'Please select size for the image'
        await state.update_data(prompt=call.text)
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
        await MyStates.SELECT_SIZE.set()

@dp.message_handler(state=MyStates.SELECT_SIZE)
async def select_size_handler(call: types.Message, state: FSMContext):
    if call.text in service.valid_sizes:
        waiting_id = await create_waiting_message(chat_id=call.chat.id)
        await bot.send_chat_action(chat_id=call.chat.id, action="upload_photo")
        filename, markup = await service.select_size( user_id=call.from_user.id, user_message=call.text, state=state)
        await bot.send_photo(chat_id=call.chat.id, photo=filename, reply_markup=markup)
        await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
        await state.finish()
    else:
        await select_prompt_handler(call=call,state=state)

@owner_only
@dp.message_handler(commands=['toggledm'])
async def toggle_dm(message: types.Message):
    if message.from_user.username != owner_id:
        await message.reply("Sorry, only the bot owner can use this command.")
        return
    global dm_enabled 
    dm_enabled = not dm_enabled
    await message.reply(f"Direct messages are now {'enabled' if dm_enabled else 'disabled'}")
        

@dp.message_handler(content_types=["text"])
async def chat_handler(call: types.Message):
    
    if not dm_enabled and call.chat.type == ChatType.PRIVATE:
        await call.reply("Direct messages are disabled by bot owner")
        return
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.chat(call=call)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    response = service.escape_markdown(response)
    await bot.send_message(chat_id=call.chat.id, text=response, parse_mode='MarkdownV2')


@dp.message_handler(content_types=["voice", "audio"])
async def voice_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response, transcript = await service.voice(user_id=call.from_user.id, file=call)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await call.reply(transcript)
    await call.reply(response)


@dp.message_handler(content_types=["photo"])
async def image_handler(call: types.Message):
    file_info = await bot.get_file(call.photo[-1].file_id)
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response, transcript = await service.image(
        user_id=call.from_user.id, file_info=file_info
    )
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await call.reply(transcript)
    await call.reply(response)


@dp.message_handler(content_types=["document"])
async def document_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.document(user_id=call.from_user.id, file=call)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await call.reply(response)


async def set_commands(user_id):
    bot_messages = service.lm.local_messages(user_id=user_id)
    commands = [
        types.BotCommand(
            command="/hello", description=f"🌟 {bot_messages['hello_description']}"
        ),
        types.BotCommand(
            command="/img", description=f"🎨 {bot_messages['img_description']}"
        ),
        types.BotCommand(
            command="/dalle",description="Generate image using DALLE-E"
        ),
        types.BotCommand(
            command="/lang", description=f"🌐 {bot_messages['lang_description']}"
        ),
        types.BotCommand(
            command="/changepersona", description=f"👤 Change character of bot"
        ),
        types.BotCommand(
            command="/clear", description=f"🧹 {bot_messages['clear_description']}"
        ),
        types.BotCommand(
            command="/help", description=f"ℹ️  {bot_messages['help_description']}"
        ),
        types.BotCommand(
            command="/changemodel", description=f"Change gpt model"
        )     
    ]
    if service.BOT_OWNER_ID != '':
        commands.append(types.BotCommand(
            command="/toggledm", description=f"Toggle Direct Message"
        ))
    
    await bot.delete_my_commands()
    await bot.set_my_commands(commands)


async def main():
    await asyncio.gather(set_commands(None), dp.start_polling())


if __name__ == "__main__":
    updater.check_for_update()
    replit_app = ReplitFlaskApp()
    replit = replit_app.run()
    if not replit:
        asyncio.run(main())

service.db.close_connection()
