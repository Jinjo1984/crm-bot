import telebot
import requests
from registration import StartHandler
from history import HistoryHandler
from menu import Menu
from create_order import OrderHandler
from personal_account import ProfileHandler
from orders_today import OrdersTodayHandler
from config import BOT_TOKEN, get_db_connection
from statistic import StatisticHandler

bot = telebot.TeleBot(BOT_TOKEN)
menu = Menu(bot)
order_handler = OrderHandler(bot)
profile_handler = ProfileHandler(bot)
orders_today_handler = OrdersTodayHandler(bot)
start_handler = StartHandler(bot, menu)
history_handler = HistoryHandler(bot)
statistic_handler = StatisticHandler(bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith("evaluate_"))
def handle_evaluation_callback(call):
    history_handler.handle_evaluation_callback(call)

@bot.message_handler(commands=['start', 'Start', 'Запуск'])
def start(message):
    start_handler.handle(message)

@bot.message_handler(func=lambda message: message.text == 'История посещений')
def history(message):
    history_handler.handle(message)

@bot.message_handler(func=lambda message: message.text == 'Запись на прием')
def order(message):
    order_handler.handle(message)

@bot.message_handler(func=lambda message: message.text == 'Профиль')
def profile(message):
    profile_handler.handle(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rating_"))
def handle_rating_callback(call):
    history_handler.handle_rating_callback(call)

@bot.message_handler(func=lambda message: message.text == 'Сегодняшние записи')
def today_orders(message):
    chat_id = message.chat.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name FROM \"user\" u JOIN role r ON u.\"roleId\" = r.id WHERE u.\"telegramId\" = %s", (str(chat_id),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and user[0] in ['Worker', 'Admin', 'SuperAdmin']:
        orders_today_handler.handle_today(message)
    else:
        bot.send_message(chat_id, "У вас нет прав для просмотра сегодняшних записей.")

@bot.message_handler(func=lambda message: message.text == 'Статистика')
def statistic(message):
    chat_id = message.chat.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name FROM \"user\" u JOIN role r ON u.\"roleId\" = r.id WHERE u.\"telegramId\" = %s", (str(chat_id),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and user[0] in ['Worker', 'Admin', 'SuperAdmin']:
        statistic_handler.handle(message)
    else:
        bot.send_message(chat_id, "У вас нет прав для просмотра статистики.")

@bot.message_handler(func=lambda message: message.text in ['Запись на прием', 'Профиль', 'Сегодняшние записи', 'История посещений', 'Статистика'])
def handle_menu(message):
    chat_id = message.chat.id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT r.name FROM \"user\" u JOIN role r ON u.\"roleId\" = r.id WHERE u.\"telegramId\" = %s", (str(chat_id),))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        menu.handle_menu_item(message, order_handler, profile_handler, orders_today_handler, statistic_handler, user[0])
    else:
        bot.send_message(chat_id, "Пожалуйста, зарегистрируйтесь.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('service_'))
def handle_service_choice(call):
    service_id = call.data.split('_')[1]
    order_handler.process_service(call.message.chat.id, service_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('master_'))
def handle_master_choice(call):
    master_id = call.data.split('_')[1]
    order_handler.process_master(call.message.chat.id, master_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_order')
def handle_confirm_order(call):
    order_handler.complete_order(call.message.chat.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_order')
def handle_cancel_order(call):
    order_handler.cancel_order(call.message.chat.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_choice(call):
    time = call.data.split('_')[1]
    order_handler.process_time(call.message.chat.id, time)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'occupied')
def handle_occupied_time(call):
    bot.answer_callback_query(call.id, "Это время уже занято.")

@bot.callback_query_handler(func=lambda call: call.data == 'edit_name')
def handle_edit_name(call):
    profile_handler.edit_name(call)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_surname')
def handle_edit_surname(call):
    profile_handler.edit_surname(call)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_secondname')
def handle_edit_secondname(call):
    profile_handler.edit_secondname(call)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_birthdate')
def handle_edit_birthdate(call):
    profile_handler.edit_birthdate(call)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'edit_phone')
def handle_edit_phone(call):
    profile_handler.edit_phone(call)
    bot.answer_callback_query(call.id)

bot.polling()