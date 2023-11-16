import os
import re
import requests
from colorama import Fore
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from dotenv import load_dotenv
from gradio_client import Client

from bot import (
    database,
    file_transcript,
    image_generator,
    language_manager,
    ocr,
    plugin_manager,
    voice_transcript,
    web_search,
    yt_transcript,
    chat_gpt,
    tts
)



class BotService:
    def __init__(self):
        load_dotenv()
        try:
            self.BOT_TOKEN = os.getenv("BOT_TOKEN")
            if self.validate_token(self.BOT_TOKEN):
                print(Fore.GREEN, f"{self.bot_username} has successfully connected to telegram")
            else:
                print(Fore.RED,'Invalid bot token')
                exit
        except Exception:
            print(Fore.RED,'please add your telegram bot token in the env file')
            exit
        try:
            self.GPT_KEY = os.getenv("GPT_KEY")
        except Exception:
            print(Fore.RED,'Please add your gpt apikey in your env file')
            exit
        try:
            self.BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")
        except Exception:
            self.BOT_OWNER_ID = ''
            print(Fore.WHITE,'Owner Id couldn\'t be determined. ToggleDM function will be disabled. To enable it add bot owner id to your environment variable')
        self.HG_TOKEN = os.getenv("HG_TOKEN", '')
        self.HG_IMG2TEXT = os.environ.get("HG_IMG2TEXT", 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large')
        self.HG_TEXT2IMAGE = os.environ.get("HG_TEXT2IMAGE", "stabilityai/stable-diffusion-2-1")
        self.DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "en")
        self.PLUGINS = os.environ.get('PLUGINS', 'true').lower() == 'true'
        self.MAX_HISTORY = int(os.environ.get("MAX_HISTORY", 15))
        self.API_BASE = os.environ.get("API_BASE", 'https://api.naga.ac/v1')
        self.DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", 'gpt-3.5')
        self.plugin_config = {'plugins': os.environ.get('ENABLED_PLUGINS', '').split(',')}
        os.makedirs("downloaded_files", exist_ok=True)
        self.db = database.Database("chatbot.db")
        self.lm = language_manager.LanguageManager(
            default_lang=self.DEFAULT_LANGUAGE, database=self.db
        )
        self.ws = web_search.WebSearch()
        self.vt = voice_transcript.VoiceTranscript()
        self.yt = yt_transcript.YoutubeTranscript()
        self.ft = file_transcript.FileTranscript()
        self.ig = image_generator.ImageGenerator(HG_IMG2TEXT=self.HG_IMG2TEXT, HG_TEXT2IMAGE=self.HG_TEXT2IMAGE)
        self.gpt = chat_gpt.ChatGPT(self.GPT_KEY,self.API_BASE,self.DEFAULT_MODEL)
        self.tts = tts.TextToSpeech(self.GPT_KEY,self.API_BASE)
        self.ocr = ocr.OCR(config=" --psm 3 --oem 3")
        self.db.create_tables()
        self.plugin = plugin_manager.PluginManager(self.plugin_config)

        if self.GPT_KEY != None:
            self.gpt.fetch_chat_models()
        self.personas = {}
        self.valid_sizes = ['256x256','512x512','1024x1024']

        self.last_msg_ids = {}
        self.last_call ={}
        self.cancel_flag = False

    def validate_token(self,bot_token):
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                response = requests.get(url)
                data = response.json()

                if response.status_code == 200 and data["ok"]:
                    self.bot_username = data["result"]["username"]
                    return True
                else:
                    return False

    async def start(self, call, waiting_id, bot):
        self.db.insert_settings(user_id=call.from_user.id)
        await self.chat(call, waiting_id, bot)
        return

    async def clear(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        self.db.delete_user_history(user_id=user_id)
        return f"🧹 {bot_messages['history_cleared']}"

    async def help(self, call, waiting_id, bot):
        await self.chat(call, waiting_id, bot)
        return

    async def lang(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        markup = self.generate_keyboard("lang")
        response = bot_messages["lang_select"]
        return response, markup

    async def select_lang(self, user_id, user_message):
        bot_messages = self.lm.local_messages(user_id=user_id)
        lang_code = user_message
        
        if lang_code in self.lm.available_lang["available_lang"]:
            self.lm.set_language(user_id, lang_code)
            markup = ReplyKeyboardRemove()
            response = (
                bot_messages["lang_selected"]
                + self.lm.available_lang["languages"][lang_code]
            )
            return response, markup
        else:
            return None, None
    
    async def changepersona(self): 
        response = "Select from the available personas"
        self.lm.load_personas(self.personas)
        markup = self.generate_keyboard('persona')
        return response, markup
    
    async def select_persona(self,user_id,user_message):
        lang, persona, model = self.db.get_settings(user_id)
        if user_message in self.personas.keys():
            self.db.update_settings(user_id,lang,persona=user_message,model=model)
            response = f'Persona set to {user_message}.'
            await self.clear(user_id)
            markup = ReplyKeyboardRemove()
        else:
            response = markup = None
        return response, markup
        
    async def changemodel(self): 
        response = "Select from the models or providers"
        markup = self.generate_keyboard('model')
        return response, markup
    
    async def select_model(self,user_id,user_message):
        lang, persona, model = self.db.get_settings(user_id)
        if user_message in self.gpt.models:
            self.db.update_settings(user_id,lang,persona,model=user_message)
            response = f'Model set to {user_message}.'
            markup = ReplyKeyboardRemove()
        else:
            response = markup = None
        return response, markup
    
    async def img(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        return bot_messages["img_prompt"]
        

    async def select_prompt(self, user_id, user_message, state):
        data = await state.get_data()
        command = data.get("command")
        markup = photo = None
        if command == '/img':
            try:
                client = Client("http://127.0.0.1:7860/")
                photo = client.predict(user_message, api_name="/predict")
            except Exception as e:
                return None, None
        elif command == '/dalle':
            photo = None
            markup = self.generate_keyboard('size')
        return photo, markup

    async def select_size(self,user_id, user_message, state):
        data = await state.get_data()
        prompt = data.get('prompt')
        photo = await self.ig.dalle_generate(prompt=prompt, size=user_message)
        markup = ReplyKeyboardRemove()
        return photo, markup

    
    async def chat(self, call, waiting_id, bot, process_prompt = ''):
        # sourcery skip: use-contextlib-suppress
        full_text = sent_text = ''
        chunk = 0
        user_id = call.from_user.id
        markup = self.generate_keyboard('text_func')
        try:
            await bot.edit_message_reply_markup(chat_id=call.chat.id,message_id=self.last_msg_ids[user_id],reply_markup=None) if user_id in self.last_msg_ids else None
        except Exception:
            pass
        self.last_call[user_id] = call
        self.last_msg_ids[user_id] = waiting_id
        user_id = call.from_user.id
        markup = self.generate_keyboard('text_func')
        self.cancel_flag = False
        try:
            await bot.edit_message_reply_markup(chat_id=call.chat.id,message_id=self.last_msg_ids[user_id],reply_markup=None) if user_id in self.last_msg_ids else None
        except Exception:
            pass
        self.last_call[user_id] = call
        self.last_msg_ids[user_id] = waiting_id
        response_stream = self.__common_generate(call=call, process_prompt=process_prompt)
        async for response in response_stream:
            if self.cancel_flag:
                 break

            if isinstance(response, str):
                full_text += response
                if full_text == '': continue
                chunk += 1
                if chunk > 10:
                    chunk = 0
                else:
                    continue
                try:
                    await bot.edit_message_text(chat_id=call.chat.id, message_id=waiting_id, text=full_text, reply_markup=markup)
                    sent_text = full_text
                except Exception:
                    continue

        if full_text not in ['', sent_text]:
            await bot.edit_message_text(chat_id=call.chat.id, message_id=waiting_id, text=full_text, reply_markup=markup) 
            self.cancel_flag = False
        
        await self.generate_tts(full_text, call, bot)
        return
            
    async def generate_tts(self, full_text, call, bot):
        audio_chunks = await self.tts.create_audio_segments(full_text)
        audio_file_path = self.tts.join_audio_segments(audio_chunks)
        audio_file = FSInputFile(audio_file_path)
        await bot.send_voice(chat_id=call.chat.id, voice=audio_file)
        os.remove(audio_file_path)
        

    async def voice(self, call, waiting_id, bot):
        user_id = call.from_user.id
        lang, persona, model = self.db.get_settings(user_id)
        bot_messages = self.lm.local_messages(user_id=user_id)
        audio_file_path = await self.vt.download_file(bot, call)
        text = await self.vt.transcribe_audio(audio_file_path, lang=lang)
        transcript = bot_messages["voice_transcribed"] + text
        prompt = bot_messages["voice_prompt"] + text
        os.remove(audio_file_path)
        call.reply(transcript)
        await self.chat(call, waiting_id, bot, process_prompt=prompt)
        return

    async def image(self, call, waiting_id, bot):
        user_id = call.from_user.id
        bot_messages = self.lm.local_messages(user_id=user_id)
        file_info = await bot.get_file(call.photo[-1].file_id)
        image_url = (
            f"https://api.telegram.org/file/bot{self.BOT_TOKEN}/{file_info.file_path}"
        )
        ocr_text = self.ocr.process_image(image_url)
        if self.HG_TOKEN and ocr_text:
            text = await self.ig.generate_imagecaption(
                url=image_url, HG_TOKEN=self.HG_TOKEN
            )
            prompt = (
                bot_messages["image_description_prompt"]
                + text
                + bot_messages["image_context_prompt"]
                + ocr_text
            )
            text += ocr_text
        elif self.HG_TOKEN:
            text = await self.ig.generate_imagecaption(
                url=image_url, HG_TOKEN=self.HG_TOKEN
            )
            ocr_text = ""
            prompt = bot_messages["image_description_prompt"] + text
        elif ocr_text:
            text = ocr_text
            prompt = bot_messages["image_context_prompt"] + ocr_text
        else:
            text = ocr_text = ""
            prompt = bot_messages["image_couldnt_read_prompt"]
        prompt += bot_messages["image_output_prompt"]
        await self.chat(call, waiting_id, bot, process_prompt=prompt)
        return


    async def document(self, call, waiting_id, bot):
        user_id = call.from_user.id
        bot_messages = self.lm.local_messages(user_id=user_id)
        file_path = await self.ft.download_file(bot, call)
        text = await self.ft.read_document(file_path)
        prompt = bot_messages["document_prompt"] + text
        os.remove(file_path)
        await self.chat(call, waiting_id, bot, process_prompt=prompt)
        return

    def escape_markdown(self,text):
        escape_chars = ['_', '-', '!', '*', '[', ']', '(', ')', '~', '>', '#', '+', '=', '{','}','|','.']
        regex = f'([{"|".join(map(re.escape, escape_chars))}])'
        return re.sub(regex, r"\\\1", text)
    
    def generate_keyboard(self,key):
        if not isinstance(key, str):
            raise ValueError("key must be a string")
        builder = ReplyKeyboardBuilder()
        if key == 'persona':
            for persona in self.personas.keys():
                builder.button(text=persona)
        elif key == 'lang':
            for lang_code in self.lm.available_lang["available_lang"]:
                builder.button(text=f"{self.lm.available_lang['languages'][lang_code]}({lang_code})")
        elif key == 'model':
            for model in self.gpt.models:
                #if model.startswith('gpt'):
                    builder.button(text=model)
        elif key == 'size':
            for size in self.valid_sizes:
                builder.button(text=size)
        elif key == 'text_func':
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄Regenerate", callback_data="regenerate")
            builder.button(text="❌Cancel", callback_data="cancel")
        return builder.as_markup()
    
    async def __common_generate(self, call, process_prompt = ''):
        user_id = call.from_user.id
        user_message = call.text
        user = call.from_user
        bot_messages = self.lm.local_messages(user_id=user_id)
        lang, persona, model = self.db.get_settings(user_id)
        self.lm.available_lang["languages"].get(
            lang,
            self.lm.available_lang["languages"]["en"],
        )
        lm = self.lm.available_lang["languages"][lang]
        history = []
        if user_message in ["/start", "/help"]:
            prompt = bot_messages["help"] + f"{lm}."
        elif process_prompt != '':
            prompt = process_prompt
        else:
            prompt = user_message


        web_text = await self.ws.extract_text_from_website(prompt)
        if web_text is not None:
            prompt = web_text
        #yt_transcript = await self.yt.get_yt_transcript(user_message, lang)
        #if yt_transcript is not None:
        #    prompt = yt_transcript
        EXTRA_PROMPT = bot_messages["EXTRA_PROMPT"]
        if user.first_name is not None:
            bot_messages["bot_prompt"] += f"You should address the user as '{user.first_name}'"
        bot_messages["bot_prompt"] += f'{bot_messages["translator_prompt"]} {lm}'
        bot_messages["bot_prompt"] += f'/n Always stay in character as {persona}'
        function = self.plugin.get_functions_specs() if self.PLUGINS else []
        should_exit = False
        fn_name = arguments = text =  ''
        self.db.insert_history(user_id=user_id, role="user", content=prompt)
        rows = self.db.get_history(user_id)[-self.MAX_HISTORY:]
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
        response_stream = self.gpt.generate_response(
            bot_messages["bot_prompt"], EXTRA_PROMPT, history,function=function, model=model
        )
        for responses in response_stream:
            if isinstance(responses, str):
                text += responses
                yield responses
                should_exit = True
                continue
            response = responses["choices"][0]["delta"]
            if 'function_call' in response:
                if 'name' in response["function_call"]:
                    fn_name += response["function_call"]["name"]
                    continue
                arguments += response["function_call"]["arguments"]
            elif 'content' in response:
                response = response['content']
                text += response
                yield response
                should_exit = True
            elif 'finish_reason' in response and text == '':
                should_exit = True
                yield 'unable to generate a response'
            else:
                yield response
        if should_exit:
            self.db.insert_history(user_id=user_id, role="assistant", content=text)
            return      

        print("Using function ",fn_name, "with arguments ", arguments)
        result = await self.plugin.call_function(fn_name,arguments)
        should_exit = False
        history.append({"role": "function", "name":fn_name, "content": result})
        for _ in range(3):
            response_stream = self.gpt.generate_response(
            bot_messages["bot_prompt"], result, history, function, model=model
            )
            for responses in response_stream:
                if isinstance(responses, str):
                    text += responses
                    yield responses
                    should_exit = True
                    continue
                response = responses["choices"][0]["delta"]
                if 'content' in response:
                    response = response['content']
                    text += response
                    yield response
                    should_exit = True
                elif 'finish_reason' in response:
                    break
                else:
                    yield response
            if should_exit:
                self.db.insert_history(user_id=user_id, role="assistant", content=text)
                return      
   