import os
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
from gradio_client import Client

from bot import (
    chat_gpt,
    database,
    file_transcript,
    image_generator,
    language_manager,
    ocr,
    voice_transcript,
    web_search,
    yt_transcript,
)


class BotService:
    def __init__(self):
        load_dotenv()
        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.HG_TOKEN = os.getenv("HG_TOKEN")
        try:
            self.BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID"))
        except:
            self.BOT_OWNER_ID = ''
            print('Owner Id couldn\'t be determined. ToggleDM function will be disabled. To enable it add bot owner id to your environment variable')
        try:
            self.HG_IMG2TEXT = os.getenv("HG_IMG2TEXT")
        except:
            self.HG_IMG2TEXT = 'https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large'
        try:
            self.DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE")
        except:
            self.DEFAULT_LANGUAGE = 'en'
        try:
            self.PLUGINS = os.getenv("PLUGINS")
        except:
            self.PLUGINS = True

        os.makedirs("downloaded_files", exist_ok=True)
        self.db = database.Database("chatbot.db")
        self.lm = language_manager.LanguageManager(
            default_lang=self.DEFAULT_LANGUAGE, database=self.db
        )
        self.ws = web_search.WebSearch(self.lm.available_lang)
        self.vt = voice_transcript.VoiceTranscript()
        self.yt = yt_transcript.YoutubeTranscript()
        self.ft = file_transcript.FileTranscript()
        self.ig = image_generator.ImageGenerator(HG_IMG2TEXT=self.HG_IMG2TEXT)
        self.gpt = chat_gpt.ChatGPT()
        self.ocr = ocr.OCR(config=" --psm 3 --oem 3 -l script//Devanagari")
        self.db.create_tables()

        self.plugins_dict = self.lm.plugin_lang["plugins_dict"]
        self.plugins_string = ""
        for plugin in self.plugins_dict:
            self.plugins_string += f"\n{plugin}: {self.plugins_dict[plugin]}"
        self.PLUGIN_PROMPT = self.lm.plugin_lang["PLUGIN_PROMPT"] + self.plugins_string

        self.personas = {}
        

    async def start(self, user_id):
        bot_messages = self.lm.local_messages(user_id)
        lang = self.db.get_settings(user_id)
        if lang in self.lm.available_lang["languages"]:
            language = self.lm.available_lang["languages"][lang]
        else:
            language = self.DEFAULT_LANGUAGE
        welcome = bot_messages["start"] + f"{language}."
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", "", history={}, prompt=welcome
        )

        return response

    async def clear(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        self.db.delete_user_history(user_id=user_id)
        response = f"🧹 {bot_messages['history_cleared']}"

        return response

    async def help(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        language = self.lm.available_lang["languages"].get(
            self.db.get_settings(user_id=user_id),
            self.lm.available_lang["languages"]["en"],
        )
        help = bot_messages["help"] + f"{language}."
        response = await self.gpt.generate_response(
            bot_messages["bot_prompt"], "", "", history={}, prompt=help
        )

        return response

    async def lang(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        markup = await self.ws.generate_keyboard("lang")
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
    def generate_keyboard(self):
        markup = ReplyKeyboardMarkup(row_width=5)
        markup.add(*[KeyboardButton(x) for x in self.personas.keys()])
        return markup
    
    async def changepersona(self): 
        response = "Select from the available personas"
        self.lm.load_personas(self.personas)
        markup = self.generate_keyboard()
        return response, markup
    
    async def select_persona(self,user_id,user_message):
        if user_message in self.personas.keys():
            self.db.update_settings(user_id,persona=user_message)
            response = f'Persona set to {user_message}.'
            await self.clear(user_id)
            markup = ReplyKeyboardRemove()
        else:
            response = markup = None
        return response, markup
        
    async def img(self, user_id):
        bot_messages = self.lm.local_messages(user_id=user_id)
        response = bot_messages["img_prompt"]
        return response

    async def select_prompt(self, user_id, user_message, state):
        bot_messages = self.lm.local_messages(user_id=user_id)
        client = Client("http://127.0.0.1:7860/")
        filename = client.predict(user_message, api_name="/predict")
        if filename:
                photo = open(filename, "rb")
        return photo

    
    async def chat(self, call):
        user_id = call.from_user.id
        user_message = call.text
        user = call.from_user
        bot_messages = self.lm.local_messages(user_id=user_id)
        lang = self.db.get_settings
        self.lm.available_lang["languages"].get(
            self.db.get_settings(user_id),
            self.lm.available_lang["languages"]["en"],
        )
        rows = self.db.get_history(user_id)[-10:]
        history = []
        prompt = user_message
        for row in rows:
            role, content = row
            history.append({"role": role, "content": content})
        bot_messages["bot_prompt"] += bot_messages["translator_prompt"]
        if user.first_name is not None:
            bot_messages["bot_prompt"] += f"And you should address the user as '{user.first_name}'"
        web_text = await self.ws.extract_text_from_website(user_message)
        if web_text is not None:
            prompt = web_text
        yt_transcript = await self.yt.get_yt_transcript(user_message, lang)
        if yt_transcript is not None:
            prompt = yt_transcript
        EXTRA_PROMPT = bot_messages["EXTRA_PROMPT"]
        text = await self.gpt.generate_response(
            self.PLUGIN_PROMPT, "plugins", EXTRA_PROMPT, {}, prompt
        )
        result, plugin_name = await self.ws.generate_query(text, self.plugins_dict)
        if result is None and plugin_name is None:
            text = await self.gpt.generate_response(
                    bot_messages["bot_prompt"], "", "", history, prompt
                )
        else:
            text = await self.gpt.generate_response(
                bot_messages["bot_prompt"], plugin_name, result, history, prompt
            )
        self.db.insert_history(user_id=user_id, role="user", content=user_message)
        self.db.insert_history(user_id=user_id, role="assistant", content=text)

        return text

    async def voice(self, user_id, file):
        lang = self.db.get_settings(user_id)
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
            bot_messages["bot_prompt"], "", "", history, prompt
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response, transcript

    async def image(self, user_id, file_info):
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
            bot_messages["bot_prompt"], "", "", history, prompt
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response, text

    async def document(self, user_id, file):
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
            bot_messages["bot_prompt"], "", "", history, prompt
        )
        self.db.insert_history(user_id=user_id, role="user", content=text)
        self.db.insert_history(user_id=user_id, role="assistant", content=response)

        return response
