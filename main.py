import asyncio
import logging
import os
import random
import sys
import requests
from updater import SelfUpdating
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_type import ChatType
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import FSInputFile, URLInputFile
from functools import wraps
from urllib.parse import urlparse

import bot_service

import subprocess
command = [sys.executable, 'interference/app.py']
process = subprocess.Popen(command, env=dict(os.environ))
service = bot_service.BotService()
updater = SelfUpdating('noes14155/Telegrambot-with-GPT4free')
storage = MemoryStorage()
bot = Bot(token=service.BOT_TOKEN)
owner_id = service.BOT_OWNER_ID
dp = Dispatcher(storage=storage)
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
    sent = await bot.send_message(chat_id=chat_id, text=f"⏳  {waiting_message}")
    asyncio.create_task(bot.send_chat_action(chat_id, "typing"))
    return sent.message_id


async def delete_waiting_message(chat_id, waiting_id):
    await bot.delete_message(chat_id=chat_id, message_id=waiting_id)


@dp.message(Command("start", "hello"))
async def start_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.start(call=call, waiting_id=waiting_id, bot=bot)
    await set_commands(user_id=call.from_user.id)


@dp.message(Command("clear"))
async def clear_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.clear(user_id=call.from_user.id)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await bot.send_message(chat_id=call.chat.id, text=response)


@dp.message(Command("help"))
async def help_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.help(call=call, waiting_id=waiting_id, bot=bot)
    
@dp.message(Command("changepersona"))
async def persona_handler(call: types.Message, state: FSMContext):
    response, markup = await service.changepersona()
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await state.set_state(MyStates.SELECT_PERSONA)

@dp.message(MyStates.SELECT_PERSONA)
async def select_persona_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_persona(user_id=call.from_user.id,user_message=call.text)
    if response and markup:
        await state.clear()
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    else:
        await persona_handler(call)


@dp.message(Command("lang"))
async def lang_handler(call: types.Message, state: FSMContext):
    response, markup = await service.lang(user_id=call.from_user.id)
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await state.set_state(MyStates.SELECT_LANG)


@dp.message(MyStates.SELECT_LANG)
async def select_lang_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_lang(
        user_id=call.from_user.id, user_message=call.text[-3:-1]
    )
    if response and markup:
        await call.answer(text=response, reply_markup=markup)
        await state.clear()
        await set_commands(user_id=call.from_user.id)
    else:
        await lang_handler(call)

@dp.message(Command("changemodel"))
async def model_handler(call: types.Message, state: FSMContext):
    response, markup = await service.changemodel()
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await state.set_state(MyStates.SELECT_MODEL)

@dp.message(MyStates.SELECT_MODEL)
async def select_model_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_model(user_id=call.from_user.id,user_message=call.text)
    if response and markup:
        await state.clear()
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    else:
        await model_handler(call)

@dp.message(Command("img","dalle"))
async def img_handler(call: types.Message, state: FSMContext):
    await state.update_data(command=call.text)
    response = await service.img(user_id=call.from_user.id)
    await bot.send_message(call.chat.id, text=response)
    await state.set_state(MyStates.SELECT_PROMPT)


@dp.message(MyStates.SELECT_PROMPT)
async def select_prompt_handler(call: types.Message, state: FSMContext):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    filename, markup = await service.select_prompt(
        user_id=call.from_user.id, user_message=call.text, state=state
    )
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    if markup is None:
        if filename:
            await bot.send_chat_action(chat_id=call.chat.id, action="upload_photo")
            photo = FSInputFile(filename)
            await bot.send_photo(chat_id=call.chat.id, photo=photo)
            os.remove(filename)
            await state.clear()
        else:
            await bot.send_message(chat_id=call.chat.id, text='Failed to generate image')
    else:
        response = 'Please select size for the image'
        await state.update_data(prompt=call.text)
        await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
        await state.set_state(MyStates.SELECT_SIZE)

@dp.message(MyStates.SELECT_SIZE)
async def select_size_handler(call: types.Message, state: FSMContext):
    if call.text in service.valid_sizes:
        waiting_id = await create_waiting_message(chat_id=call.chat.id)
        await bot.send_chat_action(chat_id=call.chat.id, action="upload_photo")
        filename, markup = await service.select_size( user_id=call.from_user.id, user_message=call.text, state=state)
        parsed = urlparse(filename)
        if parsed.scheme and parsed.netloc:
            filename = URLInputFile(filename)
            await bot.send_photo(chat_id=call.chat.id, photo=filename, reply_markup=markup)
        else: 
            await bot.send_message(chat_id=call.chat.id, text=filename, reply_markup=markup)
        await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
        await state.clear()
    else:
        await select_prompt_handler(call=call,state=state)

@owner_only
@dp.message(Command('toggledm'))
async def toggle_dm(message: types.Message):
    if message.from_user.username != owner_id:
        await message.reply("Sorry, only the bot owner can use this command.")
        return
    global dm_enabled 
    dm_enabled = not dm_enabled
    await message.reply(f"Direct messages are now {'enabled' if dm_enabled else 'disabled'}")
    logging.info(
            f"Direct Messages {'enabled' if dm_enabled else 'disabled'} by (id: {message.from_user.id})")
        
@dp.callback_query(F.data == "regenerate")
async def regenerate(callback: types.CallbackQuery):
    if callback.from_user.id not in service.last_call or callback.from_user.id not in service.last_msg_ids:
        return
    #delete previous message
    service.db.delete_last_2_user_history(callback.from_user.id)
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=service.last_msg_ids[callback.from_user.id])
    # Regenerate response
    waiting_id = await create_waiting_message(chat_id=callback.message.chat.id)  
    await service.chat(call=service.last_call[callback.from_user.id], waiting_id=waiting_id, bot=bot)

@dp.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery):
    service.cancel_flag = True

@dp.message(F.content_type.in_({'text'}))
async def chat_handler(call: types.Message):
    logging.info(
            f'New message received from user {call.from_user.full_name} (id: {call.from_user.id})')
        
    if not dm_enabled and call.chat.type == ChatType.PRIVATE:
        await call.reply("Direct messages are disabled by bot owner")
        return
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.chat(call=call, waiting_id=waiting_id, bot=bot)
    

@dp.message(F.content_type.in_({'voice','audio'}))
async def voice_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.voice(call=call, waiting_id=waiting_id, bot=bot)


@dp.message(F.content_type.in_({'photo'}))
async def image_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.image(call=call, waiting_id=waiting_id, bot=bot)
    

@dp.message(F.content_type.in_({'document'}))
async def document_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    await service.document(call=call, waiting_id=waiting_id, bot=bot)
    

async def set_commands(user_id):
    bot_messages = service.lm.local_messages(user_id=user_id)
    commands = [
        types.BotCommand(
            command="/hello",
            description=f"🌟 {bot_messages['hello_description']}",
        ),
        types.BotCommand(
            command="/img", description="🎨 Generate image custom model"
        ),
        types.BotCommand(
            command="/dalle", description="🎨 Generate image using DALLE-E"
        ),
        types.BotCommand(
            command="/lang",
            description=f"🌐 {bot_messages['lang_description']}",
        ),
        types.BotCommand(
            command="/changepersona", description="👤 Change character of bot"
        ),
        types.BotCommand(
            command="/clear",
            description=f"🧹 {bot_messages['clear_description']}",
        ),
        types.BotCommand(
            command="/help",
            description=f"ℹ️  {bot_messages['help_description']}",
        ),
        types.BotCommand(
            command="/changemodel", description="Change gpt model"
        ),
    ]
    if service.BOT_OWNER_ID != '':
        commands.append(
            types.BotCommand(
                command="/toggledm", description="Toggle Direct Message"
            )
        )
    response = requests.head(f"{service.API_BASE}/images/generations")
    if response.status_code == 404:
        commands = [command for command in commands if command.command != "/dalle"]
        
    await bot.delete_my_commands()
    await bot.set_my_commands(commands)

async def main():
    await asyncio.gather(set_commands(None), dp.start_polling(bot))

if __name__ == "__main__":
    updater.check_for_update()
    asyncio.run(main())


service.db.close_connection()
