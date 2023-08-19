import datetime
import os
import yaml
class LanguageManager:
    def __init__(self, default_lang, database):
        self.DEFAULT_LANGUAGE = default_lang
        self.db_connection = database
        self.available_lang = {}
        self.plugin_lang = {}
        self.load_available_languages()
        self.load_default_language()
    def load_available_languages(self):
        if os.path.exists("./language_files/languages.yml"):
            with open("./language_files/languages.yml", "r", encoding="utf8") as f:
                self.available_lang = yaml.safe_load(f)
        else:
            print("languages.yml does not exist")
            exit()
    def load_default_language(self):
        if os.path.exists(f"./language_files/{self.DEFAULT_LANGUAGE}.yml"):
            with open(
                f"language_files/{self.DEFAULT_LANGUAGE}.yml", "r", encoding="utf8"
            ) as file:
                self.plugin_lang = yaml.safe_load(file)
        else:
            print(f"{self.DEFAULT_LANGUAGE}.yml does not exist")
            exit()
    def set_language(self, user_id, lang):
        if not user_id:
            print("user_id does not exist")
        language,persona,model = self.db_connection.get_settings(user_id)
        if language:
            self.db_connection.update_settings(user_id, lang,persona,model)
        else:
            self.db_connection.insert_settings(user_id, lang,persona,model)
    def local_messages(self, user_id):
        lang, persona, model = self.db_connection.get_settings(user_id)
        if not lang:
            lang = self.DEFAULT_LANGUAGE
            self.db_connection.insert_settings(user_id, lang)
        language_file_path = f"./language_files/{lang}.yml"
        if os.path.exists(language_file_path):
            with open(language_file_path, "r", encoding="utf-8") as file:
                bot_messages = yaml.safe_load(file)
        else:
            print(f"{language_file_path} does not exist, Using English")
            bot_messages = {}
        personas = {}
        self.load_personas(personas)
        if persona and personas.get(persona):
            bot_messages["bot_prompt"] = personas[persona]
        bot_messages["bot_prompt"] += f"\n\nWhen replying to the user you should act as the above given persona\nIt's currently {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        return bot_messages
    def load_personas(self, personas):
        for file_name in os.listdir("personas"):
            if file_name.endswith('.txt'):
                file_path = os.path.join("personas", file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read()
                    persona = file_name.split('.')[0]
                    personas[persona] = file_content