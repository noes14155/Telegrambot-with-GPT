import datetime
import os
import yaml
class LanguageManager:
    """
    The LanguageManager class is responsible for managing languages and loading language files in a Python application.
    """

    def __init__(self, default_lang: str, database):
        """
        Initializes the LanguageManager instance with the default language and a database connection.

        Args:
            default_lang (str): The default language.
            database: The database connection object.
        """
        self.DEFAULT_LANGUAGE = default_lang
        self.db_connection = database
        self.available_lang = {}
        self.plugin_lang = {}
        self.load_available_languages()
        self.load_default_language()

    def load_available_languages(self):
        """
        Loads the available languages from the "languages.yml" file.
        """
        language_file_path = "./language_files/languages.yml"
        if os.path.exists(language_file_path):
            with open(language_file_path, "r", encoding="utf8") as f:
                self.available_lang = yaml.safe_load(f)
        else:
            print("languages.yml does not exist")
            exit()

    def load_default_language(self):
        """
        Loads the default language from a YAML file based on the default language specified during initialization.
        """
        language_file_path = f"./language_files/{self.DEFAULT_LANGUAGE}.yml"
        if os.path.exists(language_file_path):
            with open(language_file_path, "r", encoding="utf8") as file:
                self.plugin_lang = yaml.safe_load(file)
        else:
            print(f"{self.DEFAULT_LANGUAGE}.yml does not exist")
            exit()

    def set_language(self, user_id: str, lang: str):
        """
        Sets the language for a user and updates the database with the new language.

        Args:
            user_id (str): The user ID.
            lang (str): The language to set for the user.
        """
        if not user_id:
            print("user_id does not exist")
        language, persona, model = self.db_connection.get_settings(user_id)
        if language:
            self.db_connection.update_settings(user_id, lang, persona, model)
        else:
            self.db_connection.insert_settings(user_id, lang, persona, model)

    def local_messages(self, user_id: str):
        """
        Retrieves localized messages for a user based on their language and persona. If the language file does not exist,
        falls back to the default language.

        Args:
            user_id (str): The user ID.

        Returns:
            dict: Localized messages for the user.
        """
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

    def load_personas(self, personas: dict):
        """
        Loads personas from text files in the "personas" directory and stores them in a dictionary.

        Args:
            personas (dict): The dictionary to store the personas.
        """
        personas_directory = "personas"
        for file_name in os.listdir(personas_directory):
            if file_name.endswith('.txt'):
                file_path = os.path.join(personas_directory, file_name)
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_content = file.read()
                    persona = file_name.split('.')[0]
                    personas[persona] = file_content