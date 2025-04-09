from Chat.config import types
from config import API_AI
from AI.functions import AIModelAPI, handle_define


base_url = "https://api.deepseek.com"
model_name = "deepseek-chat"
model = AIModelAPI(API_AI, base_url, model_name)

# Обработчик всех сообщений
async def handle_message(message: types.Message):
    if not message.text:
        return

    user_input = message.text.strip()

    # === Приватный чат: бот отвечает всегда ===
    if message.chat.type == "private":
        ai_response = model.get_response(user_input)
        await message.reply(ai_response)
        return

    # === Групповой чат: бот отвечает на сообщения с /assistant ===
    if message.chat.type == "supergroup":
        if message.text.startswith("/bot"):
            text = user_input.split(" ", 1)[1]
            if text:

                ai_response = await handle_define(model, text, message.chat.id, "AI/embeddings_data/")

                await message.reply(ai_response)
                return
