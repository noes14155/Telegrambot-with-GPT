import os
import re
import requests
from colorama import Fore
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
from gradio_client import Client

from bot import (
    database,
    file_transcript,
    image_generator,
    language_manager,
    ocr,
    voice_transcript,
    web_search,
    yt_transcript,
)
from bot import chat_gpt


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
        except:
            print(Fore.RED,'please add your telegram bot token i the env file')
            exit
        self.HG_TOKEN = os.getenv("HG_TOKEN")
        try:
            self.CHIMERAGPT_KEY = os.getenv("CHIMERAGPT_KEY")
        except:
            print(Fore.RED,'Please add your chimeragpt apikey in your env file')
            exit
        try:
            self.BOT_OWNER_ID = os.getenv("BOT_OWNER_ID")
        except:
            self.BOT_OWNER_ID = ''
            print(Fore.WHITE,'Owner Id couldn\'t be determined. ToggleDM function will be disabled. To enable it add bot owner id to your environment variable')
        
        self.HG_IMG2TEXT = os.environ.get("HG_IMG2TEXT", 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large')
        self.DEFAULT_LANGUAGE = os.environ.get("DEFAULT_LANGUAGE", "en")
        
        self.PLUGINS = bool(os.environ.get("PLUGINS", True))
        
        os.makedirs("downloaded_files", exist_ok=True)
        self.db = database.Database("chatbot.db")
        self.lm = language_manager.LanguageManager(
            default_lang=self.DEFAULT_LANGUAGE, database=self.db
        )
        self.ws = web_search.WebSearch()
        self.vt = voice_transcript.VoiceTranscript()
        self.yt = yt_transcript.YoutubeTranscript()
        self.ft = file_transcript.FileTranscript()
        self.ig = image_generator.ImageGenerator(HG_IMG2TEXT=self.HG_IMG2TEXT)
        self.gpt = chat_gpt.ChatGPT(self.CHIMERAGPT_KEY)
        self.ocr = ocr.OCR(config=" --psm 3 --oem 3 -l script//Devanagari")
        self.db.create_tables()

        self.plugins_dict = self.lm.plugin_lang["plugins_dict"]
        self.plugins_string = ""
        for plugin in self.plugins_dict:
            self.plugins_string += f"\n{plugin}: {self.plugins_dict[plugin]}"
        self.PLUGIN_PROMPT = self.lm.plugin_lang["PLUGIN_PROMPT"] + self.plugins_string
        if self.CHIMERAGPT_KEY != None:
            self.gpt.fetch_chat_models()
            
        self.personas = {}
        self.valid_sizes = ['256x256','512x512','1024x1024']

    def validate_token(self,bot_token):
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                response = requests.get(url)
                data = response.json()

                if response.status_code == 200 and data["ok"]:
                    self.bot_username = data["result"]["username"]
                    return True
                else:
                    return False

    async def start(self, user_id):
        bot_messages = self.lm.local_messages(user_id)
        lang, persona, model = self.db.get_settings(user_id)
        if lang in self.lm.available_lang["languages"]:
            language = self.lm.available_lang["languages"][lang]
        else:
            language = self.DEFAULT_LANGUAGE
            model = 'gpt-3.5-turbo-16k'
            self.db.insert_settings(user_id=user_id)
        welcome = bot_messages["start"] + f"{language}."
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", history={}, prompt=welcome, model=model
        )
        return response

    async def clear(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        self.db.delete_user_history(user_id=user_id)
        response = f"🧹 {bot_messages['history_cleared']}"

        return response

    async def help(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        lang, persona, model = self.db.get_settings(user_id)
        language = self.lm.available_lang["languages"].get(
            lang,
            self.lm.available_lang["languages"]["en"],
        )
        help = bot_messages["help"] + f"{language}."
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", history={}, prompt=help, model=model
        )
        return response

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
        response = bot_messages["img_prompt"]
        return response

    async def select_prompt(self, user_id, user_message, state):
        data = await state.get_data()
        command = data.get("command")
        markup = photo = None
        bot_messages = self.lm.local_messages(user_id=user_id)
        if command == '/img':
            client = Client("http://127.0.0.1:7860/")
            photo = client.predict(user_message, api_name="/predict")
            
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

    
    async def chat(self, call):
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
        rows = self.db.get_history(user_id)[-10:]
        history = []
        prompt = user_message
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
        
        
        web_text = await self.ws.extract_text_from_website(user_message)
        if web_text is not None:
            prompt = web_text
        yt_transcript = await self.yt.get_yt_transcript(user_message, lang)
        if yt_transcript is not None:
            prompt = yt_transcript
        EXTRA_PROMPT = bot_messages["EXTRA_PROMPT"]
        text = await self.gpt.generate_response(
            self.PLUGIN_PROMPT, EXTRA_PROMPT, {}, prompt, model=model
        )
        result, plugin_name = await self.ws.generate_query(text, self.plugins_dict)
        if user.first_name is not None:
            bot_messages["bot_prompt"] += f"You should address the user as '{user.first_name}'"
        bot_messages["bot_prompt"] += f"You should reply to the user in {lm} as a native. Even if the user queries in another language reply only in {lm}. Completely translated."

        if result is None and plugin_name is None:
            text = await self.gpt.generate_response(
                    bot_messages["bot_prompt"], "", history, prompt, model=model
                )
        else:
            text = await self.gpt.generate_response(
                bot_messages["bot_prompt"], result, history, prompt, model=model
            )
        self.db.insert_history(user_id=user_id, role="user", content=user_message)
        self.db.insert_history(user_id=user_id, role="assistant", content=text)

        return text

    async def voice(self, user_id, file):
        lang, persona, model = self.db.get_settings(user_id)
        bot_messages = self.lm.local_messages(user_id=user_id)
        bot_messages["bot_prompt"] += bot_messages["translator_prompt"]
        rows = self.db.get_history(user_id)[-10:]
        history = []
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
        audio_file_path = await self.vt.download_file(file)
        text = await self.vt.transcribe_audio(audio_file_path, lang=lang)
        transcript = bot_messages["voice_transcribed"] + text
        prompt = bot_messages["voice_prompt"] + text
        os.remove(audio_file_path)
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", history, prompt, model=model
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response, transcript

    async def image(self, user_id, file_info):
        lang, persona, model = self.db.get_settings(user_id)
        bot_messages = self.lm.local_messages(user_id=user_id)
        bot_messages["bot_prompt"] += bot_messages["translator_prompt"]
        rows = self.db.get_history(user_id)[-10:]
        history = []
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
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
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", history, prompt, model=model
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response, text

    async def document(self, user_id, file):
        lang, persona, model = self.db.get_settings(user_id)
        bot_messages = self.lm.local_messages(user_id=user_id)
        bot_messages["bot_prompt"] += bot_messages["translator_prompt"]
        rows = self.db.get_history(user_id)[-10:]
        history = []
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
        file_path = await self.ft.download_file(file)
        text = await self.ft.read_document(file_path)
        prompt = bot_messages["document_prompt"] + text
        os.remove(file_path)
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", history, prompt, model=model
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response

    def escape_markdown(self,text):
        escape_chars = ['_', '-', '!', '*', '[', ']', '(', ')', '~', '>', '#', '+', '=', '{','}','|','.']
        regex = r"([%s])" % "|".join(map(re.escape, escape_chars))
        return re.sub(regex, r"\\\1", text)
    
    def generate_keyboard(self,key):
        if not isinstance(key, str):
            raise ValueError("key must be a string")
        markup = ReplyKeyboardMarkup(row_width=5)
        if key == 'persona':
            markup.add(*[KeyboardButton(x) for x in self.personas.keys()])
        elif key == 'lang':
            markup.add(
                *(
                    KeyboardButton(f"{self.lm.available_lang['languages'][lang_code]}({lang_code})")
                    for lang_code in self.lm.available_lang["available_lang"]
                )
            )
        elif key == 'model':
            markup.add(*[KeyboardButton(x) for x in self.gpt.models])
        elif key == 'size':
            markup.add(*[KeyboardButton(x) for x in self.valid_sizes])
        return markup