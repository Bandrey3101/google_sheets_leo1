from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('Зафиксировать расход')
b2 = KeyboardButton('Внести поступления')
b3 = KeyboardButton('ЛК')
b6 = KeyboardButton('Подтвердить')
#b7 = KeyboardButton('Редактировать')
b8 = KeyboardButton('Отменить')
b9 = KeyboardButton('Назад')
b10 = KeyboardButton('Баланс')
b11 = KeyboardButton('История транзакций')
b12 = KeyboardButton('Список объектов')
#Расходы
b13 = KeyboardButton('Черновые материалы')
b14 = KeyboardButton('Организационные расходы')
b15 = KeyboardButton('Климат')
b16 = KeyboardButton('Обстановка')
b17 = KeyboardButton('Оплата работы')
b18 = KeyboardButton('Спец. Монтаж')
b19 = KeyboardButton('Другое')
b20 = KeyboardButton('Чистовые материалы')
b21 = KeyboardButton('Пропустить')
#Поступления
b4 = KeyboardButton('Наличные')
b5 = KeyboardButton('Общий счет')


client_1 = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b1, b2, b10, b11, b12)
expenses = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b20, b13, b14, b15, b16, b17, b18, b19, b9,
                                                                      b12)
incomes = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b4, b5, b9, b12)
objects = ReplyKeyboardMarkup(resize_keyboard=True).add(b12)
editor = ReplyKeyboardMarkup(resize_keyboard=True).add(b6, b9, b12)
back = ReplyKeyboardMarkup(resize_keyboard=True).add(b9, b12)
propusk = ReplyKeyboardMarkup(resize_keyboard=True).add(b9, b21, b12)

