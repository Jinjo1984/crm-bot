from datetime import datetime
from config import get_db_connection
import re
import uuid

class StartHandler:
    def __init__(self, bot, menu):
        self.bot = bot
        self.menu = menu

    def handle(self, message):
        chat_id = message.chat.id
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT r.name
                FROM "user" u
                JOIN role r ON u."roleId" = r.id
                WHERE u."telegramId" = %s
            """, (str(chat_id),))
            user_role_name_data = cur.fetchone()

            if user_role_name_data:
                role_name = user_role_name_data[0]
                self.menu.show_menu(chat_id, role_name)
            else:
                self.bot.send_message(chat_id, "Добро пожаловать! Давайте зарегистрируемся. Введите ваше Имя:")
                self.bot.register_next_step_handler(message, self.process_name)
        except Exception as e:
            self.bot.send_message(chat_id, f"Произошла ошибка при проверке регистрации: {str(e)}")
        finally:
            cur.close()
            conn.close()

    def process_name(self, message):
        chat_id = message.chat.id
        name = message.text
        self.bot.send_message(chat_id, "Введите вашу фамилию:")
        self.bot.register_next_step_handler(message, self.process_surname, name)

    def process_surname(self, message, name):
        chat_id = message.chat.id
        surname = message.text
        self.bot.send_message(chat_id, "Введите ваше отчество:")
        self.bot.register_next_step_handler(message, self.process_secondname, name, surname)

    def process_secondname(self, message, name, surname):
        chat_id = message.chat.id
        secondname = message.text
        self.bot.send_message(chat_id, "Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):")
        self.bot.register_next_step_handler(message, self.process_birthdate, name, surname, secondname)

    def process_birthdate(self, message, name, surname, secondname):
        chat_id = message.chat.id
        birthdate_str = message.text

        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', birthdate_str):
            self.bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
            self.bot.register_next_step_handler(message, self.process_birthdate, name, surname, secondname)
            return

        try:
            birthdate = datetime.strptime(birthdate_str, '%d.%m.%Y').date()
        except ValueError:
            self.bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
            self.bot.register_next_step_handler(message, self.process_birthdate, name, surname, secondname)
            return

        self.bot.send_message(chat_id, "Введите ваш номер телефона (только цифры):")
        self.bot.register_next_step_handler(message, self.process_phone, name, surname, secondname, birthdate)

    def process_phone(self, message, name, surname, secondname, birthdate):
        chat_id = message.chat.id
        phone = message.text

        if not re.match(r'^\d+$', phone):
            self.bot.send_message(chat_id, "Неверный формат номера. Введите только цифры:")
            self.bot.register_next_step_handler(message, self.process_phone, name, surname, secondname, birthdate)
            return

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            now = datetime.now()
            user_id = str(uuid.uuid4())
            
            cur.execute("SELECT id FROM role WHERE name = 'User'")
            user_role_id_data = cur.fetchone()
            if not user_role_id_data:
                raise ValueError("Роль 'User' не найдена в базе данных. Пожалуйста, создайте её.")
            user_role_id = user_role_id_data[0]

            cur.execute("""
                INSERT INTO "user" (
                    id, "telegramId", "lastName", "firstName", "middleName",
                    "birthDate", login, email, password, "roleId", "createdAt", "updatedAt"
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, str(chat_id), surname, name, secondname,
                birthdate, phone, f'{phone}@example.com', 'password', user_role_id, now, now
            ))
            conn.commit()
            self.bot.send_message(chat_id, "Регистрация завершена!")
            self.menu.show_menu(chat_id, 'User')
        except Exception as e:
            conn.rollback()
            self.bot.send_message(chat_id, f"Произошла ошибка при регистрации: {e}")
        finally:
            cur.close()
            conn.close()