import os
import sqlite3


class Database:
    def __init__(self, db_file):
        if not os.path.exists(db_file):
            open(db_file, "a").close()
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self):
        settings_query = """CREATE TABLE IF NOT EXISTS settings 
             (user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT 'en',
                persona TEXT DEFAULT 'Julie_friend',
                "model"	TEXT DEFAULT 'gpt-4')"""
        
        history_query = """CREATE TABLE IF NOT EXISTS history 
             (user_id INTEGER, role TEXT, content TEXT)"""
        self.conn.execute(settings_query)
        self.conn.execute(history_query)
        self.conn.commit()

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def insert_settings(self, user_id, lang='en', persona='Julie_friend',model='gpt-3.5-turbo'):
        query = """INSERT OR IGNORE INTO settings (user_id, lang, persona, model)
                 VALUES (?, ?, ?, ?)"""
        self.conn.execute(query, (user_id, lang, persona,model))
        self.conn.commit()

    def update_settings(self, user_id, lang='en', persona='Julie_friend',model='gpt-3.5-turbo'):
        query = """UPDATE settings SET lang=?, persona=?, model=? WHERE user_id=?"""
        self.conn.execute(query, (lang, persona, model, user_id))
        self.conn.commit()

    def insert_history(self, user_id, role, content):
        query = """INSERT INTO history (user_id, role, content)
                 VALUES (?, ?, ?)"""
        self.conn.execute(query, (user_id, role, content))
        self.conn.commit()

    def get_settings(self, user_id):
        query = """SELECT lang, persona, model FROM settings WHERE user_id=?"""
        row = self.conn.execute(query, (user_id,)).fetchone()
        if row:
            lang, persona, model = row
            return lang, persona, model
        else:
            return None, None, None

    def get_history(self, user_id):
        query = """SELECT role, content FROM history WHERE user_id=?"""
        rows = self.conn.execute(query, (user_id,)).fetchall()
        return rows

    def delete_user_history(self, user_id):
        query = """DELETE FROM history WHERE user_id=?"""
        self.conn.execute(query, (user_id,))
        self.conn.commit()