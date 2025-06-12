import telebot
import uuid
from datetime import datetime
from config import get_db_connection

class HistoryHandler:
    def __init__(self, bot):
        self.bot = bot
        self.current_evaluation = {}

    def handle(self, message):
        chat_id = message.chat.id
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute('SELECT "id" FROM "user" WHERE "telegramId" = %s', (str(chat_id),))
            client = cur.fetchone()

            if not client:
                self.bot.send_message(chat_id, "История посещений пуста.")
                return

            cur.execute("""
                SELECT sr.id, s.name, u."firstName", u."lastName", sr."dateTime"
                FROM "serviceRecord" sr
                JOIN service s ON sr."serviceId" = s.id
                JOIN "user" u ON sr."workerId" = u.id
                WHERE sr."userId" = %s
                ORDER BY sr."dateTime" DESC
            """, (client[0],))
            service_records = cur.fetchall()

            if service_records:
                message_text = "История посещений:\n\n"
                for record in service_records:
                    message_text += (
                        f"Услуга: {record[1]}\n"
                        f"Мастер: {record[2]} {record[3]}\n"
                        f"Дата: {record[4].strftime('%d.%m.%Y')}\n"
                        f"Время: {record[4].strftime('%H:%M')}\n\n"
                    )
                self.bot.send_message(chat_id, message_text)

                for record in service_records:
                    self.send_evaluation_button(chat_id, record[0], record[1])
            else:
                self.bot.send_message(chat_id, "История посещений пуста.")

        finally:
            cur.close()
            conn.close()

    def send_evaluation_button(self, chat_id, record_id, service_name):
        markup = telebot.types.InlineKeyboardMarkup()
        evaluation_button = telebot.types.InlineKeyboardButton(
            f"Оценить {service_name}",
            callback_data=f"evaluate_{record_id}"
        )
        markup.add(evaluation_button)
        self.bot.send_message(chat_id, "Оцените посещение:", reply_markup=markup)

    def handle_evaluation_callback(self, call):
        record_id = call.data.split('_')[1]
        self.current_evaluation[call.message.chat.id] = {'record_id': record_id}
        self.send_rating_buttons(call.message.chat.id)

    def send_rating_buttons(self, chat_id):
        markup = telebot.types.InlineKeyboardMarkup()
        for rating in range(1, 6):
            markup.add(telebot.types.InlineKeyboardButton(
                str(rating),
                callback_data=f"rating_{rating}"
            ))
        self.bot.send_message(chat_id, "Выберите оценку (1-5):", reply_markup=markup)

    def handle_rating_callback(self, call):
        rating = int(call.data.split('_')[1])
        self.current_evaluation[call.message.chat.id]['rating'] = rating
        self.bot.send_message(call.message.chat.id, "Введите комментарий (необязательно):")
        self.bot.register_next_step_handler(call.message, self.process_comment)

    def process_comment(self, message):
        chat_id = message.chat.id
        comment = message.text
        record_id = self.current_evaluation[chat_id]['record_id']
        rating = self.current_evaluation[chat_id]['rating']

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT "userId", "serviceId"
                FROM "serviceRecord"
                WHERE id = %s
            """, (record_id,))
            record = cur.fetchone()

            if record:
                client_id, service_id = record
                cur.execute("""
                    INSERT INTO review (
                        id,  comment, "userId", "serviceId"
                    ) VALUES (%s, %s, %s, %s)
                """, (
                    str(uuid.uuid4()),
                    # rating,
                    comment,
                    client_id,
                    service_id,
                ))
                conn.commit()
                self.bot.send_message(chat_id, f"Спасибо за оценку ({rating}) и комментарий!")
            else:
                self.bot.send_message(chat_id, "Ошибка: запись не найдена")

        except Exception as e:
            conn.rollback()
            self.bot.send_message(chat_id, f"Произошла ошибка: {str(e)}")
        finally:
            cur.close()
            conn.close()
            if chat_id in self.current_evaluation:
                del self.current_evaluation[chat_id]
