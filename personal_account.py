import telebot
import re
from datetime import datetime
from config import get_db_connection

class ProfileHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle(self, message):
        chat_id = message.chat.id
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT "firstName", "lastName", "middleName", "birthDate", login
                FROM "user"
                WHERE "telegramId" = %s
            """, (str(chat_id),))
            user = cur.fetchone()

            if user:
                self.show_profile(chat_id, user)
            else:
                self.bot.send_message(chat_id, "Профиль не найден. Пожалуйста, зарегистрируйтесь.")
        finally:
            cur.close()
            conn.close()

    def show_profile(self, chat_id, user):
        message = "Ваш профиль:\n\n"
        message += f"Имя: {user[0]}\n"
        message += f"Фамилия: {user[1]}\n"
        message += f"Отчество: {user[2]}\n"
        message += f"Дата рождения: {user[3].strftime('%d.%m.%Y')}\n"
        message += f"Номер телефона: {user[4]}\n"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Изменить имя", callback_data="edit_name"))
        markup.add(telebot.types.InlineKeyboardButton("Изменить фамилию", callback_data="edit_surname"))
        markup.add(telebot.types.InlineKeyboardButton("Изменить отчество", callback_data="edit_secondname"))
        markup.add(telebot.types.InlineKeyboardButton("Изменить дату рождения", callback_data="edit_birthdate"))
        markup.add(telebot.types.InlineKeyboardButton("Изменить номер телефона", callback_data="edit_phone"))

        self.bot.send_message(chat_id, message, reply_markup=markup)

    def edit_name(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, "Введите новое имя:")
        self.bot.register_next_step_handler(call.message, self.process_new_name, chat_id)

    def process_new_name(self, message, chat_id):
        name = message.text
        self.update_user_field(chat_id, 'firstName', name)
        self.bot.send_message(chat_id, "Имя изменено.")
        self.handle(message)

    def edit_surname(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, "Введите новую фамилию:")
        self.bot.register_next_step_handler(call.message, self.process_new_surname, chat_id)

    def process_new_surname(self, message, chat_id):
        surname = message.text
        self.update_user_field(chat_id, 'lastName', surname)
        self.bot.send_message(chat_id, "Фамилия изменена.")
        self.handle(message)

    def edit_secondname(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, "Введите новое отчество:")
        self.bot.register_next_step_handler(call.message, self.process_new_secondname, chat_id)

    def process_new_secondname(self, message, chat_id):
        secondname = message.text
        self.update_user_field(chat_id, 'middleName', secondname)
        self.bot.send_message(chat_id, "Отчество изменено.")
        self.handle(message)

    def edit_birthdate(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, "Введите новую дату рождения (ДД.ММ.ГГГГ):")
        self.bot.register_next_step_handler(call.message, self.process_new_birthdate, chat_id)

    def process_new_birthdate(self, message, chat_id):
        birthdate_str = message.text
        if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', birthdate_str):
            self.bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
            self.bot.register_next_step_handler(message, self.process_new_birthdate, chat_id)
            return

        try:
            birthdate = datetime.strptime(birthdate_str, '%d.%m.%Y').date()
            self.update_user_field(chat_id, 'birthDate', birthdate)
            self.bot.send_message(chat_id, "Дата рождения изменена.")
            self.handle(message)
        except ValueError:
            self.bot.send_message(chat_id, "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:")
            self.bot.register_next_step_handler(message, self.process_new_birthdate, chat_id)

    def edit_phone(self, call):
        chat_id = call.message.chat.id
        self.bot.send_message(chat_id, "Введите новый номер телефона (только цифры):")
        self.bot.register_next_step_handler(call.message, self.process_new_phone, chat_id)

    def process_new_phone(self, message, chat_id):
        phone = message.text
        if not re.match(r'^\d+$', phone):
            self.bot.send_message(chat_id, "Неверный формат номера. Введите только цифры:")
            self.bot.register_next_step_handler(message, self.process_new_phone, chat_id)
            return

        self.update_user_field(chat_id, 'login', phone)
        self.bot.send_message(chat_id, "Номер телефона изменен.")
        self.handle(message)

    def update_user_field(self, chat_id, field, value):
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute(f"""
                UPDATE "user"
                SET "{field}" = %s
                WHERE "telegramId" = %s
            """, (value, str(chat_id)))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
            conn.close()