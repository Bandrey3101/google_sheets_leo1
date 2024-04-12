from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import admin_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import gspread
import logging
import traceback
import sys
from google.oauth2 import service_account


credentials = service_account.Credentials.from_service_account_file(
    'creds_mail.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])


client = gspread.authorize(credentials)


class FSMadmin(StatesGroup):
    new_obj = State()


ID = None


async def admin_start(message: types.Message):
    global ID
    ID = message.from_user.id
    await bot.send_message(message.from_user.id, "Вы находитесь в режиме администратора",
                           reply_markup=admin_kb.admin_main)


async def admin_objects(message: types.Message):
    try:
        if message.from_user.id == ID:
            await bot.send_message(message.from_user.id, 'Список объектов: ')
            with open('sheets_list.txt', 'r', encoding='windows-1251') as f:
                sheets = f.read().splitlines()
                for sheet_name in sheets:
                    await bot.send_message(message.from_user.id, f'{sheet_name}', reply_markup=InlineKeyboardMarkup().
                                           add(InlineKeyboardButton(f'Удалить', callback_data=f'del {sheet_name}')))
        else:
            await bot.send_message(message.from_user.id, "Введите пароль")
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")


#@dp.callback_query_handler(lambda c: c.data.startswith('del'))
async def delete_object(callback_query: types.CallbackQuery):
    with open('sheets_list.txt', 'r', encoding='windows-1251') as f:
        sheets = f.read().splitlines()
    # Получаем данные из колбэка
    data = callback_query.data
    user_id = callback_query.from_user.id
    # Извлекаем название объекта, которое нужно удалить
    object_name = data.replace('del ', '')
    # Проверяем, что пользователь имеет право на удаление объекта
    if user_id == ID:
        if object_name in sheets:
            sheets.remove(object_name)
            with open('sheets_list.txt', 'w', encoding='windows-1251') as f:
                for item in sheets:
                    f.write("%s\n" % item)
                await bot.send_message(user_id, f'Объект "{object_name}" удален.')
        else:
            await bot.send_message(user_id, f'Объект "{object_name}" не найден в списке.')
    else:
        await bot.send_message(user_id, 'Введите пароль')


async def back_admin(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == FSMadmin.new_obj.state:
        print(current_state)
        await state.finish()
        await bot.send_message(message.from_user.id, "Вы находитесь в режиме администратора",
                               reply_markup=admin_kb.admin_main)

async def add_object(message: types.Message):
    await FSMadmin.new_obj.set()
    await bot.send_message(message.from_user.id, 'Введите название объекта (Название должно точно совпадать с названием '
                                                 'таблицы в GoogleSheets):', reply_markup=admin_kb.back)


async def save_object(message: types.Message, state: FSMContext):
    try:
        await bot.send_message(message.from_user.id, "Сохраняю данные...")
        with open('sheets_list.txt', 'a', encoding='windows-1251') as file:
            # Записываем название новой таблицы в конец файла
            file.write(message.text + '\n')
        await bot.send_message(message.from_user.id, f"Объект {message.text} добавлен\n",
                               reply_markup=admin_kb.admin_main)
        await state.finish()
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")


# Создание копии шаблонной таблицы
def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands='123321')
    dp.register_message_handler(admin_objects, text='Удалить объект')
    dp.register_message_handler(back_admin, state="*", text='назад')
    dp.register_message_handler(add_object, text="Добавить объект")
    dp.register_callback_query_handler(delete_object, lambda query: query.data.startswith('del '))
    dp.register_message_handler(save_object, state=FSMadmin.new_obj)



