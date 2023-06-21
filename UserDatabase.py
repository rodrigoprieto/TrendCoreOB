import sqlite3
from sqlite3 import Error

class UserDatabase:
    def __init__(self, db_file):

        """ create a database connection to a SQLite database """
        self.conn = None
        try:
            self.conn = sqlite3.connect(db_file)
            self.conn.row_factory = sqlite3.Row
        except Error as e:
            print(e)

        if self.conn:
            self.create_table()

    def create_table(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, language_code TEXT, 
            wallsize INTEGER, distance REAL)
        ''')

    def insert_user(self, user):
        c = self.conn.cursor()
        c.execute('''
            INSERT INTO users VALUES(?,?,?,?,?,?)
        ''', (user.id,
              user.username,
              user.first_name,
              user.language_code,
              250000,  # default wallsize
              5.0))   # default distance
        self.conn.commit()

    def get_user(self, id):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE id=?', (id,))
        return c.fetchone()

    def update_wallsize(self, user, wallsize):
        c = self.conn.cursor()
        c.execute('UPDATE users SET wallsize = ? WHERE id = ?', (wallsize, user.id))
        self.conn.commit()

    def update_distance(self, user, distance):
        c = self.conn.cursor()
        c.execute('UPDATE users SET distance = ? WHERE id = ?', (distance, user.id))
        self.conn.commit()


