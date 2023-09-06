import os
import sqlite3


class Database:
    """
    A class that provides methods for interacting with a SQLite database.
    """

    def __init__(self, db_file: str) -> None:
        """
        Initializes the Database class by creating a connection to the SQLite database
        and creating the necessary tables if they don't exist.

        Args:
            db_file (str): The path to the SQLite database file.
        """
        if not os.path.exists(db_file):
            open(db_file, "a").close()
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self) -> None:
        """
        Creates the settings and history tables in the database if they don't exist.
        """
        settings_query = """CREATE TABLE IF NOT EXISTS settings 
             (user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT 'en',
                persona TEXT DEFAULT 'Julie_friend',
                "model"	TEXT DEFAULT 'gpt-4')"""
        
        history_query = """CREATE TABLE IF NOT EXISTS history 
             (user_id INTEGER, role TEXT, content TEXT)"""
        self.conn.execute(settings_query)
        self.conn.execute(history_query)
        self.conn.commit()

    def close_connection(self) -> None:
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()

    def insert_settings(self, user_id: int, lang: str = 'en', persona: str = 'Julie_friend', model: str = 'gpt-3.5-turbo') -> None:
        """
        Inserts settings for a user into the settings table.

        Args:
            user_id (int): The ID of the user.
            lang (str, optional): The language setting. Defaults to 'en'.
            persona (str, optional): The persona setting. Defaults to 'Julie_friend'.
            model (str, optional): The model setting. Defaults to 'gpt-3.5-turbo'.
        """
        query = """INSERT OR IGNORE INTO settings (user_id, lang, persona, model)
                 VALUES (?, ?, ?, ?)"""
        self.conn.execute(query, (user_id, lang, persona, model))
        self.conn.commit()

    def update_settings(self, user_id: int, lang: str = 'en', persona: str = 'Julie_friend', model: str = 'gpt-3.5-turbo') -> None:
        """
        Updates settings for a user in the settings table.

        Args:
            user_id (int): The ID of the user.
            lang (str, optional): The language setting. Defaults to 'en'.
            persona (str, optional): The persona setting. Defaults to 'Julie_friend'.
            model (str, optional): The model setting. Defaults to 'gpt-3.5-turbo'.
        """
        query = """UPDATE settings SET lang=?, persona=?, model=? WHERE user_id=?"""
        self.conn.execute(query, (lang, persona, model, user_id))
        self.conn.commit()

    def insert_history(self, user_id: int, role: str, content: str) -> None:
        """
        Inserts history for a user into the history table.

        Args:
            user_id (int): The ID of the user.
            role (str): The role of the user.
            content (str): The content of the history.
        """
        query = """INSERT INTO history (user_id, role, content)
                 VALUES (?, ?, ?)"""
        self.conn.execute(query, (user_id, role, content))
        self.conn.commit()

    def get_settings(self, user_id: int) -> tuple[str, str, str]:
        """
        Retrieves settings for a user from the settings table.

        Args:
            user_id (int): The ID of the user.

        Returns:
            tuple[str, str, str]: The language, persona, and model settings for the user.
        """
        query = """SELECT lang, persona, model FROM settings WHERE user_id=?"""
        row = self.conn.execute(query, (user_id,)).fetchone()
        if row:
            lang, persona, model = row
            return lang, persona, model
        else:
            return None, None, None

    def get_history(self, user_id: int) -> list[tuple[str, str]]:
        """
        Retrieves history for a user from the history table.

        Args:
            user_id (int): The ID of the user.

        Returns:
            list[tuple[str, str]]: A list of tuples containing the role and content of the history.
        """
        query = """SELECT role, content FROM history WHERE user_id=?"""
        rows = self.conn.execute(query, (user_id,)).fetchall()
        return rows

    def delete_user_history(self, user_id: int) -> None:
        """
        Deletes history for a user from the history table.

        Args:
            user_id (int): The ID of the user.
        """
        query = """DELETE FROM history WHERE user_id=?"""
        self.conn.execute(query, (user_id,))
        self.conn.commit()