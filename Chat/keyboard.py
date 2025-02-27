from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Общая клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/about")],
        [KeyboardButton(text="Создать группу"), KeyboardButton(text="Добавить студента")]
    ],
    resize_keyboard=True
)
