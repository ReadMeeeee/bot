import yaml
import requests
from bs4 import BeautifulSoup

class YamlParser:
    def __init__(self, base_url, headers=None):
        self.base_url = base_url
        self.headers = headers or {}

    def fetch_page(self, path):
        """Собирает полный URL, делает HTTP-запрос и возвращает HTML-ответ."""
        url = self.base_url + path
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def parse_page(self, html, selector):
        """Ищет элемент по селектору и возвращает его текст (или None)."""
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select_one(selector)
        return element.text if element else None

def load_config(config_path="config.yaml"):
    """Загружает конфигурацию из YAML-файла."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config