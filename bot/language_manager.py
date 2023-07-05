import datetime
import os

import yaml


class LanguageManager:
    def __init__(self, default_lang, database):
        self.DEFAULT_LANGUAGE = default_lang
        self.db_connection = database

        if os.path.exists("language_files/languages.yml"):
            with open("language_files/languages.yml", "r", encoding="utf8") as f:
                self.available_lang = yaml.safe_load(f)
        else:
            print("languages.yml does not exist")
            exit

        if os.path.exists(f"language_files/{self.DEFAULT_LANGUAGE}.yml"):
            with open(
                f"language_files/{self.DEFAULT_LANGUAGE}.yml", "r", encoding="utf8"
            ) as file:
                self.plugin_lang = yaml.safe_load(file)
        else:
            print(f"{self.DEFAULT_LANGUAGE}.yml does not exist")
            exit

    def set_language(self, user_id, lang):
        if not user_id:
            print("user_id is does not exist")

        language = self.db_connection.get_settings(user_id)
        if language:
            self.db_connection.update_settings(user_id, lang)
        else:
            self.db_connection.insert_settings(user_id, lang)

    def local_messages(self, user_id):
        if user_id:
            lang = self.db_connection.get_settings(user_id)
        else:
            lang = self.DEFAULT_LANGUAGE
        language_file_path = f"./language_files/{lang}.yml"
        if os.path.exists(language_file_path):
            with open(language_file_path, "r", encoding="utf-8") as file:
                global bot_messages
                bot_messages = yaml.safe_load(file)
        else:
            print(f"{language_file_path} does not exist, Using English")
            exit
        bot_messages[
            "bot_prompt"
        ] += f"\n\nIt's currently {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        return bot_messages
