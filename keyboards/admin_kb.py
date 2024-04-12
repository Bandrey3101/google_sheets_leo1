from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('Добавить объект')
b2 = KeyboardButton('Удалить объект')
b3 = KeyboardButton('Выход')
b4 = KeyboardButton('назад')


admin_main = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b1, b2, b3)
back = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1).add(b4)
