import os
from dotenv import load_dotenv

load_dotenv()

model = "Qwen/Qwen2-1.5B-Instruct"

API_TG = os.getenv("API_TG")
API_AI = os.getenv("API_AI")
