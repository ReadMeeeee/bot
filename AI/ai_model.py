import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

model = "Qwen/Qwen2-1.5B-Instruct"
BNB_8BIT_CONFIG = BitsAndBytesConfig(load_in_8bit=True)
BNB_4BIT_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)


class AIModel:
    def __init__(self, model_name: str, tokenizer = None, quantization_config = None,
                 dtype: torch.dtype = torch.bfloat16, trust_remote_code: bool = False, device = None):
        """
        Класс для инициализации модели ИИ по параметрам:

        :param model_name: Имя модели
        :param tokenizer: Токенизатор (по умолчанию токенизатор заданной модели)
        :param quantization_config: Настройки квантизации (по умолчанию None)
        :param dtype: Тип данных для модели (по умолчанию torch.bfloat16)
        :param trust_remote_code: Доверие к сторонним репозиториям (по умолчанию False)
        :param device: Устройство для загрузки модели (по умолчанию адаптивно, изначально - 'cuda')
        """
        self.model_name = model_name
        self.tokenizer = tokenizer if tokenizer is not None else AutoTokenizer.from_pretrained(model_name)
        self.quantization_config = quantization_config
        self.dtype = dtype
        self.trust_remote_code = trust_remote_code
        self.device = device if device is not None else ("cuda" if torch.cuda.is_available() else "cpu")

        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map=self.device,
                quantization_config=self.quantization_config,
                torch_dtype=self.dtype,
                trust_remote_code=self.trust_remote_code
            )
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки модели {model_name}: {e}")


    def _preprocess(self, chat: list[dict[str, str]]):
        """
        Преобразует входной текст в формат, необходимый пользователю и модели.
        """

        text = self.tokenizer.apply_chat_template(
            chat,
            tokenize=False,
            add_generation_prompt=True
        )

        return self.tokenizer(text, return_tensors="pt").to(self.device)


    def get_response(self, message: str, _chat: list[dict[str, str]] = None, role: str = None, instruction: str = None,
                     max_tokens=50, temperature=1.0,
                     repetition_penalty=1.0, no_repeat_ngram_size=0):
        """
        Функция для генерации ответа на запрос к ИИ

        :param message: Строка с сообщением пользователя
        :param _chat: Параметр - словарь, уже содержащий роль и инструкции (для внутриклассового пользования)
        :param role: Роль для ИИ
        :param instruction: Инструкция для обработки текста при помощи ИИ
        :param max_tokens: Максимальное количество токенов в ответе
        :param temperature: Параметр, контроля случайности генерации. Выше - случайнее
        :param repetition_penalty: Коэффициент штрафа за повторение токенов
        :param no_repeat_ngram_size: Размер n-граммы, запрещающей повторы слов

        :return: Строка со сгенерированным ответом
        """
        if _chat is None:
            _chat = [
            {"role": "system", "content": f"{role}"},
            {"role": "user", "content": f"{instruction} {message}"}
            ]

        model_inputs = self._preprocess(_chat)
        attention_mask = model_inputs.attention_mask if hasattr(model_inputs, 'attention_mask') else None

        generated_ids = self.model.generate(
            model_inputs.input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_tokens,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            no_repeat_ngram_size=no_repeat_ngram_size,
            do_sample=True
        )

        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        return self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


    def load(self, path: str):
        """
        Загружает модель и токенизатор из указанного пути.

        :param path: путь для загрузки
        """
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModelForCausalLM.from_pretrained(path, device_map=self.device)
        print(f"Модель и токенизатор загружены из {path}")

# TODO
# через классы -> в ООП
# туда же и get-send
# чтобы не было комментирование и раскомментирования

# function calling

# Обучить модель на форматированный вывод: {задача{параметры}, информация для ИИ из сторонних источников, ответ ИИ}
#                                                              информацию доставать функцией и класть RAGом
