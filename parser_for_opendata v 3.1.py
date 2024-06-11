import requests
from lxml import html
from urllib.parse import urljoin
import os
import re
from tqdm import tqdm

# Регулярні вирази для шаблонів URL другого і третього рівнів
level2_pattern = re.compile(r"https://data\.loda\.gov\.ua/dataset/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}")
level3_pattern = re.compile(r"https://data\.loda\.gov\.ua/dataset/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/resource/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")

# Функція для перевірки наявності елементу на сторінці
def check_element(url, xpath):
    response = requests.get(url)
    if response.status_code == 200:
        tree = html.fromstring(response.content)
        element = tree.xpath(xpath)
        if element:
            return True
    return False

# Функція для отримання всіх посилань на сторінці
def get_links(url):
    response = requests.get(url)
    if response.status_code == 200:
        tree = html.fromstring(response.content)
        links = tree.xpath('//a[@href]')
        return [urljoin(url, link.get('href')) for link in links]
    return []

# Початкова сторінка та xpath елементу для перевірки
base_url = "https://data.loda.gov.ua/dataset/"
xpath = "/html/body/div[2]/div/div[2]/section/div/div[1]/ul/li[2]"

# Список для зберігання результатів
results = []

# Збір сторінок другого рівня з усіх підсторінок головної сторінки
level2_urls = set()
for page_num in range(1, 11):
    page_url = f"{base_url}?page={page_num}"
    level2_urls.update(url for url in get_links(page_url) if level2_pattern.match(url))

# Збір сторінок третього рівня та перевірка наявності елементу
for url in tqdm(level2_urls, desc="Processing URLs", unit="URL"):
    level3_urls = [url for url in get_links(url) if level3_pattern.match(url)]
    for sub_url in level3_urls:
        # Перевірка, чи не міститься вже такий результат в списку results
        if not any(result[1] == sub_url for result in results):
            results.append((url, sub_url, check_element(sub_url, xpath)))

# Запис результатів у текстовий файл у тій же папці, де знаходиться скрипт
script_dir = os.path.dirname(os.path.realpath(__file__))
results_file_path = os.path.join(script_dir, 'results.txt')

# Заголовки стовпців
header = "Level 2 URL\tLevel 3 URL\tFound\n"

with open(results_file_path, 'w') as file:
    # Запис заголовків
    file.write(header)
    # Запис результатів
    for level2_url, url, found in results:
        file.write(f"{level2_url}\t{url}\t{'Found' if found else 'Not Found'}\n")

print(f"Результати збережено у файл {results_file_path}")
