from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
import asyncio
import crud_functions
import re

api = " "
bot = Bot(token= api)
dp = Dispatcher(bot, storage= MemoryStorage())

kb_1 = ReplyKeyboardMarkup(resize_keyboard=True)
button_1 = KeyboardButton(text='Регистрация')
button_2 = KeyboardButton(text='Купить')
button_3 = KeyboardButton(text='Информация')
button_4 = KeyboardButton(text='Рассчитать')
kb_1.row(button_1, button_2, button_3, button_4)


kb_2 = InlineKeyboardMarkup(resize_keyboard=True)
button_1 = InlineKeyboardButton(text='Рассчитать норму калорий', callback_data='calories')
button_2 = InlineKeyboardButton(text='Формулы расчёта', callback_data='formulas')
kb_2.add(button_1)
kb_2.add(button_2)

kb_3 = InlineKeyboardMarkup(resize_keyboard=True)
button_1 = InlineKeyboardButton(text='Product1', callback_data='product_buying')
button_2 = InlineKeyboardButton(text='Product2', callback_data='product_buying')
button_3 = InlineKeyboardButton(text='Product3', callback_data='product_buying')
button_4 = InlineKeyboardButton(text='Product4', callback_data='product_buying')
kb_3.insert(button_1)
kb_3.insert(button_2)
kb_3.insert(button_3)
kb_3.insert(button_4)

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()

@dp.message_handler(text='Регистрация')
async def sing_up(message):
    await message.answer("Введите имя пользователя (только латинский алфавит):")
    await RegistrationState.username.set()

@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if crud_functions.is_included(username):
        await message.answer("Пользователь существует, введите другое имя:")
    else:
        await state.update_data(username=username)
        await message.answer("Введите свой email:")
        await RegistrationState.email.set()

@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        await message.answer("Введите корректный email (пример: example@mail.com):")
        return
    await state.update_data(email=email)
    await message.answer("Введите свой возраст:")
    await RegistrationState.age.set()

@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if age <= 0:
            raise ValueError("Возраст должен быть больше 0.")
    except ValueError:
        await message.answer("Введите корректный возраст (целое число больше 0):")
        return
    await state.update_data(age=age)
    data = await state.get_data()
    try:
        crud_functions.add_user(data['username'], data['email'], data['age'])
    except Exception as e:
        await message.answer(f"Произошла ошибка при регистрации: {e}")
        return
    await message.answer("Регистрация завершена! Добро пожаловать!", reply_markup=kb_1)
    await state.finish()

@dp.message_handler(text=['Купить'])
async def get_buying_list(message):
    products = crud_functions.get_all_products()
    number = 1
    for i in products:
        with open(f'{number}.jpg', "rb") as img:
            await message.answer_photo(img, f'Продукт {number}')
        number += 1
        await message.answer(f'Название: {i[1]} | Описание: {i[2]} | Цена: {i[3]}')
    await message.answer('Выберите продукт для покупки:', reply_markup=kb_3)

@dp.callback_query_handler(text="product_buying")
async def send_confirm_message(call):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()

@dp.message_handler(text=['Рассчитать'])
async def main_menu(message):
    print("Выберите опцию:")
    await message.answer("Выберите опцию:", reply_markup=kb_2)

@dp.callback_query_handler(text=['formulas'])
async def get_formulas(call):
    print("(10 х вес в кг) + (6,25 х рост в см) – (5 х возраст в годах)")
    await call.message.answer("Формула Миффлина-Сан Жеора:(10 х вес в кг) + (6,25 х рост в см) – (5 х возраст в годах)")
    await call.answer()

@dp.message_handler(commands=['start'])
async def start_message(message):
    print("Привет! Я бот помогающий твоему здоровью.")
    await message.answer("Привет! Я бот помогающий твоему здоровью.", reply_markup=kb_1)

@dp.message_handler(text=['Информация'])
async def inform(message):
    await message.answer("Это информация о боте!")

@dp.callback_query_handler(text=['calories'])
async def set_age(call):
    print("Введите свой возраст в годах:")
    await call.message.answer("Введите свой возраст в годах:")
    await call.answer()
    await UserState.age.set()

@dp.message_handler(state=UserState.age)
async def set_growth(message, state):
    await state.update_data(age=message.text)
    print("Введите свой рост в см:")
    await message.answer("Введите свой рост в см:")
    await UserState.growth.set()

@dp.message_handler(state=UserState.growth)
async def set_weight(message, state):
    await state.update_data(growth=message.text)
    print("Введите свой вес в кг:")
    await message.answer("Введите свой вес в кг:")
    await UserState.weight.set()

@dp.message_handler(state=UserState.weight)
async def send_calories(message, state):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    calories = 10 * float(data['weight']) + 6.25 * float(data['growth']) - 5 * float(data['age'])
    await message.answer(f'По формуле Миффлина-Сан Жеора норма для Вас - {calories} калорий')
    await state.finish()

@dp.message_handler(text=['Urban'])
async def urban_message(message):
    print("Urban message")

@dp.message_handler()
async def all_message(message):
    print("Введите команду /start, чтобы начать общение.")
    await message.answer("Введите команду /start, чтобы начать общение.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
