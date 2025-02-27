from AI.config import device
from AI.Deep_Seek_R1 import model as model_main, tokenizer as tokenizer_main


def generate_response(user_message, model, tokenizer, max_tokens=50, temperature=1.0,
                      repetition_penalty=1.0, no_repeat_ngram_size=0):
    chat = [
        {"role": "system", "content": "Ты AI помощник старосты в университете."},
        {"role": "user", "content": f"Если данное сообщение: \" {user_message}\"\n"
                                    f"просит отправить расписание - ОТПРАВЬ ТОЛЬКО \"0\"\nЕсли оно "
                                    f"просит отправить домашнее задание - ОТПРАВЬ ТОЛЬКО \"1\"\nЕсли оно "
                                    f"просит отправить новости по учебе - ОТПРАВЬ ТОЛЬКО \"2\"\n Иначе "}
    ]

    text = tokenizer.apply_chat_template(
        chat,
        tokenize=False,
        add_generation_prompt=True
    )

    model_inputs = tokenizer([text], return_tensors="pt").to(device)
    attention_mask = model_inputs.attention_mask if hasattr(model_inputs, 'attention_mask') else None

    generated_ids = model.generate(
        model_inputs.input_ids,
        attention_mask = attention_mask,
        max_new_tokens=max_tokens,
        temperature=temperature,
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,
        do_sample=True
    )

    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    # Преобразование токенов в человеко-читаемый текст
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


# Функция обработки ИИ
def get_ai_response(user_message: str) -> str:
    response = generate_response(user_message, model_main, tokenizer_main,
                                 max_tokens=400, temperature=0.6,
                                 repetition_penalty=1.1, no_repeat_ngram_size=3)
    return f"{response}\n\n"
