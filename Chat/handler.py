from Chat.config import types
from AI.AI_funcs import get_ai_response


# Обработчик всех сообщений
async def handle_message(message: types.Message):
    if not message.text:
        return

    user_input = message.text.strip()

    # === Приватный чат: бот отвечает всегда ===
    if message.chat.type == "private":
        ai_response = get_ai_response(user_input)
        await message.reply(ai_response)
        return

    # === Групповой чат: бот отвечает на сообщения с /assistant ===
    if message.chat.type == "supergroup":
        if message.text.startswith("/assistant"):
            text = user_input.split(" ", 1)[1]
            if text:
                ai_response = get_ai_response(text)
                await message.reply(ai_response)
                return
