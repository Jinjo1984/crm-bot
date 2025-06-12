import telebot
import psycopg2
from datetime import datetime, timedelta
from config import get_db_connection

class OrdersTodayHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle_today(self, message):
        chat_id = message.chat.id
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT s.name, u."firstName", u."lastName", sr."dateTime"
                FROM "serviceRecord" sr
                JOIN service s ON sr."serviceId" = s.id
                JOIN "user" u ON sr."workerId" = u.id
                WHERE sr."dateTime" >= %s AND sr."dateTime" < %s
                ORDER BY sr."dateTime"
            """, (today, tomorrow))

            records = cur.fetchall()

            if records:
                message_text = "Сегодняшние записи:\n\n"
                for record in records:
                    dt = record[3]
                    message_text += (
                        f"Услуга: {record[0]}\n"
                        f"Мастер: {record[1]} {record[2]}\n"
                        f"Дата: {dt.strftime('%d.%m.%Y')}\n"
                        f"Время: {dt.strftime('%H:%M')}\n\n"
                    )
                self.bot.send_message(chat_id, message_text)
            else:
                self.bot.send_message(chat_id, "На сегодня записей нет.")

        finally:
            cur.close()
            conn.close()