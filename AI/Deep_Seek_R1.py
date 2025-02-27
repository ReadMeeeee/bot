from AI.config import load_model, dtype


model_name = "Qwen/Qwen2-1.5B-Instruct"
model, tokenizer = load_model(model_name, torch_dtype=dtype)

# from AI.config import BNB_8BIT_CONFIG
# model_name = "deepseek-ai/DeepSeek-R1"
# model, tokenizer = load_model(model_name, quantization_config=BNB_8BIT_CONFIG, trust_remote_code=True)
