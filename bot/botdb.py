import sqlite3

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self):
        settings_query = '''CREATE TABLE IF NOT EXISTS settings 
             (user_id INTEGER PRIMARY KEY, api_name TEXT, model TEXT)'''
        history_query = '''CREATE TABLE IF NOT EXISTS history 
             (user_id INTEGER, role TEXT, content TEXT)'''
        self.conn.execute(settings_query)
        self.conn.execute(history_query)
        self.conn.commit()

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def insert_settings(self, user_id, api_name, model):
        query = '''INSERT OR IGNORE INTO settings (user_id, api_name, model)
                 VALUES (?, ?, ?)'''
        self.conn.execute(query, (user_id, api_name, model))
        self.conn.commit()

    def update_settings(self, user_id, api_name=None, model=None):
        if api_name:
            query = '''UPDATE settings SET api_name=? WHERE user_id=?'''
            self.conn.execute(query, (api_name, user_id))
        if model:
            query = '''UPDATE settings SET model=? WHERE user_id=?'''
            self.conn.execute(query, (model, user_id))
        self.conn.commit()

    def insert_history(self, user_id, role, content):
        query = '''INSERT INTO history (user_id, role, content)
                 VALUES (?, ?, ?)'''
        self.conn.execute(query, (user_id, role, content))
        self.conn.commit()

    def get_settings(self, user_id):
        query = '''SELECT api_name, model FROM settings WHERE user_id=?'''
        row = self.conn.execute(query, (user_id,)).fetchone()
        if row:
            api_name, model = row
            return api_name, model

    def get_history(self, user_id):
        query = '''SELECT role, content FROM history WHERE user_id=?'''
        rows = self.conn.execute(query, (user_id,)).fetchall()
        return rows