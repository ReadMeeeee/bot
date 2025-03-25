from data_parse_yaml import *


config = load_config()
parsed_data = []
parsers_conf = config['parsers']
headers = parsers_conf.get('headers', {})

for site_key, site_conf in config['parsers'].items():
    if site_key == 'headers':
        continue
    base_url = site_conf.get('base_url')
    endpoints = site_conf.get('endpoints', {})
    site_parser = YamlParser(base_url, headers=headers)

    for endpoint_key, endpoint_conf in endpoints.items():
        path = endpoint_conf.get("path")
        selectors = endpoint_conf.get("selectors", {})
        try:
            html_content = site_parser.fetch_page(path)
        except Exception as e:
            print(f"Ошибка при получении страницы {path}: {e}")
            continue

        parsed_text = {}
        for selector_name, selector_value in selectors.items():
            extracted_text = site_parser.parse_page(html_content, selector_value)
            parsed_text[selector_name] = extracted_text

        # Формируем запись с данными и метаданными
        record = {
            "site": site_key,
            "endpoint": endpoint_key,
            "path": path,
            "full_url": base_url + path,
            "text": parsed_text,
            # Можно добавить дополнительные поля, если необходимо
        }
        parsed_data.append(record)


import json

with open("parsed_data.json", "w", encoding="utf-8") as f:
    json.dump(parsed_data, f, ensure_ascii=False, indent=2)

print("Итоговые данные сохранены в parsed_data.json")
