import asyncio
import logging
import os
import random

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import bot_service
from replit_detector import ReplitFlaskApp

service = bot_service.BotService()
storage = MemoryStorage()
bot = Bot(token=service.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


class MyStates(StatesGroup):
    SELECT_PROMPT = State()
    SELECT_STYLE = State()
    SELECT_RATIO = State()
    SELECT_LANG = State()
    SELECT_PERSONA = State()


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


@dp.message_handler(commands=["img"])
async def img_handler(call: types.Message):
    response = await service.img(user_id=call.from_user.id)
    await bot.send_message(call.chat.id, text=response)
    await MyStates.SELECT_PROMPT.set()


@dp.message_handler(state=MyStates.SELECT_PROMPT)
async def select_prompt_handler(call: types.Message, state: FSMContext):
    response, markup = await service.select_prompt(
        user_id=call.from_user.id, user_message=call.text, state=state
    )
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    await MyStates.next()


@dp.message_handler(state=MyStates.SELECT_STYLE)
async def select_style_handler(call: types.Message, state: FSMContext):
    response, markup, isSuccess = await service.select_style(
        user_id=call.from_user.id, user_message=call.text, state=state
    )
    await bot.send_message(chat_id=call.chat.id, text=response, reply_markup=markup)
    if isSuccess == False:
        await MyStates.SELECT_STYLE.set()
    else:
        await MyStates.SELECT_RATIO.set()


@dp.message_handler(state=MyStates.SELECT_RATIO)
async def select_ratio_image(call: types.Message, state: FSMContext):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response, photo, isSuccess, markup, filename = await service.select_ratio(
        user_id=call.from_user.id, user_message=call.text, state=state
    )
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    if isSuccess and photo:
        await bot.send_chat_action(chat_id=call.chat.id, action="upload_photo")
        await bot.send_photo(chat_id=call.chat.id, photo=photo, reply_markup=markup)
        await bot.send_message(chat_id=call.chat.id, text=response)
        os.remove(filename)
    else:
        await bot.send_message(chat_id=call.chat.id, text=response)
    await state.finish()


@dp.message_handler(content_types=["text"])
async def chat_handler(call: types.Message):
    waiting_id = await create_waiting_message(chat_id=call.chat.id)
    response = await service.chat(call=call)
    await delete_waiting_message(chat_id=call.chat.id, waiting_id=waiting_id)
    await bot.send_message(chat_id=call.chat.id, text=response)


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
        
    ]
    await bot.delete_my_commands()
    await bot.set_my_commands(commands)


async def main():
    await asyncio.gather(set_commands(None), dp.start_polling())


if __name__ == "__main__":
    replit_app = ReplitFlaskApp()
    replit = replit_app.run()
    if not replit:
        asyncio.run(main())

service.db.close_connection()
