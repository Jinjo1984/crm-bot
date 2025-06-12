import telebot

class Menu:
    def __init__(self, bot):
        self.bot = bot

    def show_menu(self, chat_id, role):
        markup = telebot.types.ReplyKeyboardMarkup(row_width=1)
        if role== 'User':
            markup.add('Запись на прием', 'История посещений', 'Профиль')
            self.bot.send_message(chat_id, "Основное меню:", reply_markup=markup)
        elif role == 'Worker':
            markup.add('Запись на прием','Сегодняшние записи','Текущая запись', 'Статистика','История посещений', 'Профиль')
            self.bot.send_message(chat_id, "Меню работника:", reply_markup=markup)
        elif role == 'Admin' or role == 'SuperAdmin': 
            markup.add('Запись на прием','Сегодняшние записи', 'Статистика', 'Профиль','История посещений')
            self.bot.send_message(chat_id, "Меню администратора:", reply_markup=markup)
        else:
            self.bot.send_message(chat_id, "Ваша роль не определена или не поддерживается.")

    def handle_menu_item(self, message, order_handler, profile_handler, orders_today_handler, statistic_handler, role, history_handler):
        try:
            if message.text == 'Запись на прием':
                order_handler.handle(message)
            elif message.text == 'Профиль':
                profile_handler.handle(message)
            elif message.text == 'Сегодняшние записи':
                if role in ['Worker', 'Admin', 'SuperAdmin']:
                    orders_today_handler.handle_today(message)
                else:
                    self.bot.send_message(message.chat.id, "У вас нет прав для просмотра сегодняшних записей.")
            elif message.text == 'История посещений':
                history_handler.handle(message)
            elif message.text == 'Статистика':
                if role in ['Admin', 'SuperAdmin']: 
                    statistic_handler.handle(message)
                else:
                    self.bot.send_message(message.chat.id, "У вас нет прав для просмотра статистики.")
        except Exception as e:
             self.bot.send_message(message.chat.id, f"Произошла ошибка при обработке пункта меню: {str(e)}")