import os
from dotenv import load_dotenv

load_dotenv()

model = "Qwen/Qwen2-1.5B-Instruct"

link_schedule = "https://schedule.sfedu.ru/APIv1/schedule/grade/"
link_news_sfedu = "https://sfedu.ru/press-center/newspage/1"
link_news_mmcs = "https://mmcs.sfedu.ru/"

API_TG = os.getenv("API_TG")
# API_AI = os.getenv("API_AI")
