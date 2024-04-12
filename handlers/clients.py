from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, ContentType
import config
from create_bot import dp, bot
from keyboards import client_kb
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
import gspread
import datetime
from asyncio import sleep
import yadisk
import os
import logging
import traceback
import sys
from google.oauth2 import service_account



logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')


credentials = service_account.Credentials.from_service_account_file(
    'creds_mail.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(credentials)

client_y = yadisk.Client(token=config.yandex)
# ник

spreadsheet_id = ''
users = []
file_bill = ""
public_url = ''
current_date = str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))


months_rus = {
    1: 'Январь',
    2: 'Февраль',
    3: 'Март',
    4: 'Апрель',
    5: 'Май',
    6: 'Июнь',
    7: 'Июль',
    8: 'Август',
    9: 'Сентябрь',
    10: 'Октябрь',
    11: 'Ноябрь',
    12: 'Декабрь'
}

# Получение текущего месяца и его названия на русском языке
current_month_num = datetime.datetime.now().month
current_month_rus = months_rus[current_month_num]


class FSMclient(StatesGroup):
    expense = State()
    summ = State()
    comment = State()
    bill = State()
    income = State()
    check = State()


async def first_start(message: types.Message):
    users.append(message.from_user.id)
    await bot.send_message(message.from_id, 'Введите пароль для доступа к боту')


# password-
async def command_start(message: types.Message):
    if message.from_user.id in users:
        await bot.send_message(message.from_user.id, "Выберите объект:", reply_markup=create_inline_keyboard())


# Функция, которая создает сообщение с встроенными кнопками на основе словаря таблиц
def create_inline_keyboard():
    try:
        keyboard = InlineKeyboardMarkup(row_width=1)
        with open('sheets_list.txt', 'r', encoding='windows-1251') as f:
            sheets = f.read().splitlines()
            for sheet_name in sheets:
                button = InlineKeyboardButton(text=sheet_name, callback_data=f'value_{sheet_name}')
                print(sheet_name)
                keyboard.add(button)
        return keyboard
    except Exception as e:
        (print(f"Снова ошибка: {e}"))
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")


# Обработчик коллбэков от кнопок
async def process_callback(callback_query: types.CallbackQuery):
    global spreadsheet_id
    await bot.answer_callback_query(callback_query.id)
    spreadsheet_id = callback_query.data.split('_')[1]
    await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                message_id=callback_query.message.message_id,
                                text=f"Вы выбрали объект: {spreadsheet_id}")
    await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=client_kb.client_1)


# text='Список объектов'
async def cancel_hand(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data.clear()
    if message.from_user.id in users:
        current_state = await state.get_state()
        if current_state is None:
            await command_start(message)
        else:
            await state.finish()
            await command_start(message)


async def back(message: types.Message, state: FSMContext):
    if message.from_user.id in users:
        current_state = await state.get_state()
        if current_state is None:
            await command_start(message)
        elif current_state == FSMclient.check.state:
            async with state.proxy() as data:
                if 'expense' in data:
                    await FSMclient.bill.set()
                    await bot.send_message(message.from_user.id, "Прикрепите чек:", reply_markup=client_kb.propusk)
                elif 'income' in data:
                    await FSMclient.comment.set()
                    await bot.send_message(message.from_user.id, "Напишите комментарий:", reply_markup=client_kb.back)
        elif current_state == FSMclient.bill.state:
            print(current_state)
            await FSMclient.comment.set()
            await bot.send_message(message.from_user.id, "Напишите комментарий:", reply_markup=client_kb.back)
        elif current_state == FSMclient.comment.state:
            print(current_state)
            await FSMclient.summ.set()
            await bot.send_message(message.from_user.id, "Введите сумму (в формате 000 или 000.00):", reply_markup=client_kb.back)
        elif current_state == FSMclient.summ.state:
            async with state.proxy() as data:
                if 'expense' in data:
                    await FSMclient.expense.set()
                    await bot.send_message(message.from_user.id, "Выберите статью расхода:",
                                           reply_markup=client_kb.expenses)
                elif 'income' in data:
                    await FSMclient.income.set()
                    await bot.send_message(message.from_user.id, "Выберите способ оплаты:", reply_markup=client_kb.incomes)
        elif current_state == FSMclient.income.state or current_state == FSMclient.expense.state:
            print(current_state)
            await state.finish()
            await bot.send_message(message.from_user.id, "Выберите действие:", reply_markup=client_kb.client_1)
        else:
            await state.finish()
            await command_start(message)


# text='Зафиксировать расход')
async def expenses(message: types.Message, state: FSMContext):
    # Отправляем сообщение с функцией перебора таблиц
    async with state.proxy() as data:
        data['operation'] = 'Расход'
    await FSMclient.expense.set()
    await bot.send_message(message.from_user.id, "Выберите статью расхода:", reply_markup=client_kb.expenses)


# text='Внести поступления'
async def incomes(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['operation'] = 'Поступление'
    # Отправляем сообщение с функцией перебора таблиц
    await FSMclient.income.set()
    await bot.send_message(message.from_user.id, "Выберите способ оплаты:", reply_markup=client_kb.incomes)


# text='Баланс'
async def balance(message: types.Message):
    try:
        sheet = client.open(spreadsheet_id).worksheet('Лист4')
        values = sheet.get_all_values()
        # Инициализируем переменные для сумм расходов и доходов
        total_expenses = 0
        total_incomes = 0
        # Проходим по каждой строке в таблице
        for row in values[1:]:  # Пропускаем первую строку с заголовками
            if row[2] == 'Расход':
                total_expenses += float(row[4].replace(',', '.'))
            elif row[2] == 'Поступление':
                total_incomes += float(row[4].replace(',', '.'))
        # Вычисляем разницу
        balance = total_incomes - total_expenses
        await bot.send_message(message.from_user.id, f"Баланс объекта {spreadsheet_id}: {balance}руб.",
                               reply_markup=client_kb.objects)
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        #bot.send_message(chat_id=410731842, text=f"Ошибка в строке: {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")


async def history(message: types.Message, state: FSMContext):
    try:
        await bot.send_message(message.from_user.id, "Транзакции выводятся по 20 шт. Чтобы получить следующие "
                                                     "20 транзакций, нажмите кнопку 'История транзакций' еще раз")
        range_of_cells = 'B2:F'  # Указываем диапазон ячеек
        sheet = client.open(spreadsheet_id).worksheet('Лист4')
        cell_values = sheet.get(range_of_cells)
        reversed_values = reversed(cell_values)  # Разворачиваем значения, чтобы начать с последней транзакции
        async with state.proxy() as data:
            if 'transaction_index' not in data:
                data['transaction_index'] = 0  # Инициализируем индекс транзакции
            # Получаем индекс следующей транзакции для отображения
            start_index = data['transaction_index']
            end_index = start_index + 20
            # Создаем список для хранения строк для вывода
            output_rows = []
            # Формируем строки для вывода транзакций
            for row in reversed_values:
                output_string = " - ".join(row)  # Формируем строку из значений в ячейках
                output_rows.append(output_string)
            # Выбираем только 10 транзакций для вывода
            transactions_to_display = output_rows[start_index:end_index]
            # Выводим транзакции пользователю
            await bot.send_message(message.from_user.id, "Транзакции:\n" + "\n".join(transactions_to_display))
            # Обновляем индекс следующей транзакции
            data['transaction_index'] = end_index
    except Exception as e:
        logging.error("Ошибка при выводе истории транзакций: %s", str(e))
        await bot.send_message(message.from_user.id, "Произошла ошибка при выводе истории транзакций.")


# сохранение статьи расходов
async def save_expenses(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = datetime.datetime.now().strftime("%d.%m.%Y")
        data['expense'] = message.text
    await FSMclient.summ.set()
    await bot.send_message(message.from_user.id, "Введите сумму (в формате 000 или 000.00):", reply_markup=client_kb.back)


# сохранение источник поступления
async def save_incomes(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = datetime.datetime.now().strftime("%d.%m.%Y")
        data['income'] = message.text
    await FSMclient.summ.set()
    await bot.send_message(message.from_user.id, "Введите сумму (в формате 000 или 000.00):", reply_markup=client_kb.back)


# сохраняем сумму
async def save_summ(message: types.Message, state: FSMContext):
    if message.text.replace('.', '').isdigit():
        async with state.proxy() as data:
            data['summ'] = message.text
        await FSMclient.comment.set()
        await bot.send_message(message.from_user.id, "Напишите комментарий:", reply_markup=client_kb.back)
    else:
        await bot.send_message(message.from_user.id, "Похоже, что вы ввели не совсем цифры", reply_markup=client_kb.back)
        await FSMclient.summ.set()
        await bot.send_message(message.from_user.id, "Введите сумму (в формате 000 или 000.00):", reply_markup=client_kb.back)


# сохраняем коммент
async def save_comment(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['comment'] = message.text
            if 'expense' in data:
                await FSMclient.bill.set()
                await bot.send_message(message.from_user.id, "Прикрепите чек:", reply_markup=client_kb.propusk)
                print('5')
            elif 'income' in data:
                data['bill'] = "-"
                await FSMclient.check.set()
                await bot.send_message(message.from_user.id, f"Проверяем:\n\nОбъект: {spreadsheet_id}\n"
                                                             f"Операция: {data['operation']}\n"
                                                             f"{data['income']}\n"
                                                             f"Cумма: {data['summ']}\n"
                                                             f"Комментарий: {data['comment']}",
                                       reply_markup=client_kb.editor)
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        #bot.send_message(chat_id=410731842, text=f"Ошибка в строке: {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")


# сохраняем чек
async def save_bill(message: types.Message, state: FSMContext):
    try:
        global file_bill
        photo_id = message.photo[-1]
        file_bill = os.path.join(os.getcwd(), f"{message.from_user.id}.jpg")
        await photo_id.download(file_bill)
        print(file_bill)
        async with state.proxy() as data:
            await FSMclient.check.set()
            await bot.send_photo(chat_id=message.from_user.id, photo=open(file_bill, 'rb'),
                                 caption=f"Проверяем:\n\nОбъект: {spreadsheet_id}\n"
                                                         f"Операция: {data['operation']}\n"
                                                         f"{data['expense']}\n"
                                                         f"Cумма: {data['summ']}\n"
                                                         f"Комментарий: {data['comment']}",
                                   reply_markup=client_kb.editor)
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        #bot.send_message(chat_id=410731842, text=f"Ошибка в строке: {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")


async def save_bill_doc(message: types.Message, state: FSMContext):
    if message.document:
        try:
            global file_bill
            # Получаем идентификатор документа
            document_id = message.document.file_id
            # Получаем информацию о документе
            document_info = await bot.get_file(document_id)
            # Скачиваем документ
            document = await bot.download_file(document_info.file_path)
            # Сохраняем документ
            file_bill = f"{message.from_user.id}_{message.document.file_name}"
            with open(file_bill, 'wb') as new_file:
                new_file.write(document.read())
            print(file_bill)
            async with state.proxy() as data:
                await FSMclient.check.set()
                # Отправляем документ
                await bot.send_document(chat_id=message.from_user.id, document=open(file_bill, 'rb'),
                                        caption=f"Проверяем:\n\nОбъект: {spreadsheet_id}\n"
                                                f"Операция: {data['operation']}\n"
                                                f"{data['expense']}\n"
                                                f"Cумма: {data['summ']}\n"
                                                f"Комментарий: {data['comment']}",
                                        reply_markup=client_kb.editor)
        except Exception as e:
            logging.error("Снова ошибка: %s", str(e))
            traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
            line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
            print(f"Ошибка в строке {line_number}: {e}")
            #bot.send_message(chat_id=410731842, text=f"Ошибка в строке: {line_number}: {e}")
            await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                          "изменится, обратитесь к разработчику")


async def bill_pass(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['bill'] = "-"
            await FSMclient.check.set()
            await bot.send_message(chat_id=message.from_user.id, text=f"Проверяем:\n\nОбъект: {spreadsheet_id}\n"
                                                         f"Операция: {data['operation']}\n"
                                                         f"{data['expense']}\n"
                                                         f"Cумма: {data['summ']}\n"
                                                         f"Комментарий: {data['comment']}",
                                   reply_markup=client_kb.editor)
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        #bot.send_message(chat_id=410731842, text=f"Ошибка в строке: {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")



async def exit_admin(message: types.Message):
    if message.from_user.id in users:
        await bot.send_message(message.from_user.id, "Вы вышли из режима администратора",
                               reply_markup=ReplyKeyboardRemove())
        await sleep(1)
        await command_start(message)


async def editor(message: types.Message, state: FSMContext):
    try:
        await bot.send_message(message.from_user.id, "Сохраняю данные...")
        sheet = client.open(spreadsheet_id).worksheet('Лист4')
        async with state.proxy() as data:
            data['check'] = message.text
            if data['check'] == 'Подтвердить':
                # Получаем значения столбца, начиная со второй строки
                column_values = sheet.col_values(1)[1:]
                # Получаем количество заполненных ячеек, начиная со второй строки
                max_row = len(column_values)
                # Увеличение текущего максимального значения на 1 для следующей строки
                next_number = max_row + 1  # Учитываем, что мы начинаем считать с второй строки
                data['id'] = next_number
                if not message.from_user.username:
                    username = 'Ник отсутствует'
                elif not message.from_user.first_name:
                    name = 'Имя отсутствует'
                else:
                    username = message.from_user.username
                    name = message.from_user.first_name
                data['user'] = f'{name} | @{username}'
                data['month'] = current_month_rus
                if 'expense' in data:
                    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg']
                    #Получаем расширение файла
                    file_extension = os.path.splitext(file_bill)[1]
                    try:
                        if 'bill' in data:
                            await bot.send_message(chat_id=-1002012707768, text=
                                                    f"Номер транзакции: {next_number}\nОбъект: {spreadsheet_id}\n"
                                                    f"Операция: {data['operation']}\n"
                                                    f"{data['expense']}\n"
                                                    f"Cумма: {data['summ']}\n"
                                                    f"Комментарий: {data['comment']}\n"
                                                    f"Пользователь: {data['user']}")
                            row_values = [
                                data['id'],
                                data['date'],
                                data['operation'],
                                data['expense'],
                                float(data['summ']),
                                data['comment'],
                                data["bill"],
                                data['user'],
                                data['month']
                            ]
                            sheet.append_row(row_values)
                            data.clear()
                        else:
                            if file_extension.lower() in image_extensions:
                                await bot.send_photo(chat_id="chat_id", photo=open(file_bill, 'rb'),
                                                         caption=f"Номер транзакции: {next_number}\nОбъект: {spreadsheet_id}\n"
                                                                 f"Операция: {data['operation']}\n"
                                                                 f"{data['expense']}\n"
                                                                 f"Cумма: {data['summ']}\n"
                                                                 f"Комментарий: {data['comment']}\n"
                                                                 f"Пользователь: {data['user']}")
                            else:
                                await bot.send_document(chat_id="chat_id", document=open(file_bill, 'rb'),
                                                        caption=f"Номер транзакции: {next_number}\nОбъект: {spreadsheet_id}\n"
                                                                f"Операция: {data['operation']}\n"
                                                                f"{data['expense']}\n"
                                                                f"Cумма: {data['summ']}\n"
                                                                f"Комментарий: {data['comment']}\n"
                                                                f"Пользователь: {data['user']}")
                            with client_y:
                                try:
                                    global public_url
                                    file_extension = os.path.splitext(file_bill)[1]
                                    # Генерируем имя файла для сохранения на Яндекс.Диск
                                    file_name_on_disk = f'чек_{str(datetime.datetime.now())}{file_extension}'
                                    file_path_on_disk = "Чеки, счета/" + file_name_on_disk
                                    print(file_path_on_disk)
                                    # Загружаем файл на Яндекс.Диск
                                    client_y.upload(file_bill, file_path_on_disk)
                                    client_y.publish(file_path_on_disk)
                                    # Получение общедоступной ссылки на файл
                                    public_url = client_y.get_meta(file_path_on_disk).public_url
                                except Exception as e:
                                    logging.error("ошибка загрузки чека: %s", str(e))
                                    await bot.send_message(message.from_user.id, 'Чек не загружен')
                                row_values = [
                                    data['id'],
                                    data['date'],
                                    data['operation'],
                                    data['expense'],
                                    float(data['summ']),
                                    data['comment'],
                                    public_url,
                                    data['user'],
                                    data['month']
                                ]
                                sheet.append_row(row_values)
                                data.clear()
                    except Exception as e:
                        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
                        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
                        print(f"Ошибка в строке {line_number}: {e}")
                        logging.error("ошибка отправки в транзакции: %s", str(e))
                        await bot.send_message(message.from_user.id, 'Ошибка при отправке транзакции в чат')
                    # if len(file_bill) > 1:
                        os.remove(file_bill)
                elif 'income' in data:
                    try:
                        await bot.send_message(chat_id="chat_id", text=
                                                        f"Номер транзакции: {next_number}\nОбъект: {spreadsheet_id}\n"
                                                        f"Операция: {data['operation']}\n"
                                                        f"{data['income']}\n"
                                                        f"Cумма: {data['summ']}\n"
                                                        f"Комментарий: {data['comment']}\n"
                                                        f"Пользователь: {data['user']}")
                    except Exception as e:
                        logging.error("ошибка отправки в транзакции: %s", str(e))
                        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
                        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
                        print(f"Ошибка в строке {line_number}: {e}")
                        await bot.send_message(message.from_user.id, 'Ошибка при отправке транзакции в чат')
                    row_values = [
                        data['id'],
                        data['date'],
                        data['operation'],
                        data['income'],
                        float(data['summ']),
                        data['comment'],
                        data['bill'],
                        data['user'],
                        data['month']
                    ]
                    sheet.append_row(row_values)
                    data.clear()
                await state.finish()
                await bot.send_message(message.from_user.id, 'Данные внесены', reply_markup=client_kb.objects)
    except Exception as e:
        logging.error("Снова ошибка: %s", str(e))
        traceback_info = traceback.extract_tb(sys.exc_info()[2])[-1]  # Получаем информацию о последнем стеке вызовов
        line_number = traceback_info[1]  # Номер строки, на которой произошла ошибка
        print(f"Ошибка в строке {line_number}: {e}")
        await bot.send_message(message.from_user.id, "Неизвестная ошибка. Попробуйте еще раз, если ничего не "
                                                      "изменится, обратитесь к разработчику")



def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(first_start, commands='start')
    dp.register_message_handler(command_start, commands='321')
    dp.register_message_handler(exit_admin, text='Выход')
    dp.register_callback_query_handler(process_callback, lambda query: query.data.startswith('value_'))
    dp.register_message_handler(expenses, text='Зафиксировать расход')
    dp.register_message_handler(incomes, text='Внести поступления')
    dp.register_message_handler(balance, text='Баланс')
    dp.register_message_handler(history, text='История транзакций')
    dp.register_message_handler(cancel_hand, state="*", text='Список объектов')
    dp.register_message_handler(back, state="*", commands='Назад')
    dp.register_message_handler(back, Text(equals='Назад', ignore_case=True), state="*")
    dp.register_message_handler(save_expenses, state=FSMclient.expense)
    dp.register_message_handler(save_incomes, state=FSMclient.income)
    dp.register_message_handler(save_summ, state=FSMclient.summ)
    dp.register_message_handler(save_comment, state=FSMclient.comment)
    dp.register_message_handler(save_bill, content_types=types.ContentType.PHOTO, state=FSMclient.bill)
    dp.register_message_handler(save_bill_doc, content_types=types.ContentType.DOCUMENT, state=FSMclient.bill)
    dp.register_message_handler(bill_pass, text="Пропустить", state=FSMclient.bill)
    dp.register_message_handler(editor, state=FSMclient.check)
