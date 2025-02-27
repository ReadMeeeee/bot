import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


dtype = torch.bfloat16
device = "cuda" if torch.cuda.is_available() else "cpu"
BNB_8BIT_CONFIG = BitsAndBytesConfig(load_in_8bit=True)
BNB_4BIT_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=dtype,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
)

def load_model(model_name, quantization_config=None, torch_dtype=None, trust_remote_code=False):
    """Загружает модель с заданными параметрами"""
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map=device,
        quantization_config=quantization_config,
        torch_dtype=torch_dtype,
        trust_remote_code=trust_remote_code
    )

    return model, tokenizer
