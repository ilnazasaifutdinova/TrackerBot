import os

# Перед импортом SSL любыми сетевыми библиотеками проверяет, что используется пакет сертификатов CA от certifi
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass

import requests
from bs4 import BeautifulSoup
import re
import discord
from discord.ext import tasks
from dotenv import load_dotenv

# Загрузка .env файла
load_dotenv()

# Загрузка переменных окружения
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

# Ссылка на ресурс
url = os.getenv('MANGA_URL')

# Добавляем заголовки (притворяемся браузером)
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

# Инициализируем счетчик глав
total_chapters = 0

# Создаём Discord клиента
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Получает номер последней главы
def get_latest_chapter():
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Основной метод: Total Chapters
        total_chapters_elem = soup.find(
            string=re.compile(r'Total Chapters', re.IGNORECASE)
        )

        if total_chapters_elem:
            parent = total_chapters_elem.parent
            if parent:
                next_span = parent.find_next('span')
                if next_span:
                    match = re.search(r'(\d+)', next_span.get_text())
                    if match:
                        return int(match.group(1))

        # Второй метод: regex по тексту
        text = re.sub(r'<!--.*?-->', '', soup.get_text())
        pattern = r'(\d+)\s*Chapters?|Chapter\s*(\d+)'
        matches = re.findall(pattern, text, re.IGNORECASE)

        chapter_numbers = [
            int(m[0] or m[1]) for m in matches if (m[0] or m[1])
        ]

        return max(chapter_numbers) if chapter_numbers else None

    except Exception as e:
        print(f"Ошибка при получении главы: {e}")
        return None

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем элемент с "Total Chapters"
        total_chapters_elem = soup.find(string=re.compile(r'Total Chapters', re.IGNORECASE))
        
        if total_chapters_elem:
            # Ищем родительский элемент
            parent = total_chapters_elem.parent
            if parent:
                # Ищем соседний <span> с числом
                next_span = parent.find_next('span')
                if next_span:
                    text = next_span.get_text(strip=True)
                    
                    # Извлекаем число из текста (например "22Chapter" или "22 Chapter")
                    match = re.search(r'(\d+)', text)
                    if match:
                        return int(match.group(1))
        
        # Если не нашли через Total Chapters, пробуем альтернативный метод
        # Убираем HTML комментарии
        all_text = re.sub(r'<!--.*?-->', '', soup.get_text())
        
        # Ищем паттерн
        pattern = r'(\d+)\s*Chapters?|Chapter\s*(\d+)'
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        
        if matches:
            chapter_numbers = []
            for match in matches:
                num = match[0] if match[0] else match[1]
                if num:
                    chapter_numbers.append(int(num))
            
            if chapter_numbers:
                return max(chapter_numbers)
        
        return None
        
    except Exception as e:
        print(f"Ошибка при получении главы: {e}")
        return None
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n=== Debug: Поиск глав (новый метод) ===")
        
        # Метод 1: Ищем элемент с "Total Chapters"
        total_chapters_elem = soup.find(string=re.compile(r'Total Chapters', re.IGNORECASE))
        
        if total_chapters_elem:
            print("Найден элемент 'Total Chapters'")
            
            # Ищем родительский элемент
            parent = total_chapters_elem.parent
            if parent:
                # Ищем соседний <span> с числом
                next_span = parent.find_next('span')
                if next_span:
                    text = next_span.get_text(strip=True)
                    print(f"Текст из span: '{text}'")
                    
                    # Извлекаем число из текста (может быть "22 Chapter" или "22Chapter")
                    match = re.search(r'(\d+)', text)
                    if match:
                        chapter_num = int(match.group(1))
                        print(f"Найдена глава: {chapter_num}")
                        print("=== Debug End ===\n")
                        return chapter_num
        
        # Метод 2: Ищем все span с классом содержащим "semibold"
        print("\nМетод 2: Поиск через классы...")
        spans = soup.find_all('span', class_=re.compile(r'semibold'))
        print(f"Найдено span с 'semibold': {len(spans)}")
        
        for i, span in enumerate(spans[:10]):
            text = span.get_text(strip=True)
            if 'chapter' in text.lower():
                print(f"  {i}: '{text}'")
                match = re.search(r'(\d+)', text)
                if match:
                    chapter_num = int(match.group(1))
                    print(f"Найдена глава методом 2: {chapter_num}")
                    print("=== Debug End ===\n")
                    return chapter_num
        
        # Метод 3: Ищем все числа рядом с "Chapter"
        print("\nМетод 3: Поиск всех чисел...")
        all_text = soup.get_text()
        
        # Убираем HTML комментарии
        all_text = re.sub(r'<!--.*?-->', '', all_text)
        
        # Ищем паттерн
        pattern = r'(\d+)\s*Chapters?|Chapter\s*(\d+)'
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        
        print(f"Совпадений после удаления комментариев: {len(matches)}")
        
        if matches:
            print(f"Первые 10: {matches[:10]}")
            
            chapter_numbers = []
            for match in matches:
                num = match[0] if match[0] else match[1]
                if num:
                    chapter_numbers.append(int(num))
            
            if chapter_numbers:
                result = max(chapter_numbers)
                print(f"Максимум: {result}")
                print("=== Debug End ===\n")
                return result
        
        print("Не удалось найти главу!")
        print("=== Debug End ===\n")
        return None
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None
    """Получает номер последней главы"""
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None
        
        # ОТЛАДКА
        print("\n=== Debug: Поиск глав ===")
        
        # Паттерн
        chapter_pattern = r'(\d+)\s*Chapters?|Chapter\s*(\d+)'
        matches = re.findall(chapter_pattern, response.text, re.IGNORECASE)
        
        print(f"Найдено совпадений с regex: {len(matches)}")
        
        if matches:
            print(f"Первые 10 совпадений: {matches[:10]}")
        
        # Извлекаем номера
        chapter_numbers = []
        for match in matches:
            num = match[0] if match[0] else match[1]
            if num:
                chapter_numbers.append(int(num))
        
        print(f"Извлечённые номера глав: {chapter_numbers[:15]}")

        if chapter_numbers:
            result = max(chapter_numbers)
            print(f"Максимальное значение (последняя глава): {result}")
            print("=== Debug End ===\n")
            return result
        
        # Если не нашли, то делается дополнительная отладка
        print("\n!!! Regex не нашёл совпадений !!!")
        print("Проверяем вручную:")
        print(f"  'Total Chapters' в HTML: {'Total Chapters' in response.text}")
        print(f"  '23Chapter' в HTML: {'23Chapter' in response.text}")
        print(f"  'Chapter 23' в HTML: {'Chapter 23' in response.text}")
        print(f"  '13 Chapter' в HTML: {'13 Chapter' in response.text}")
        
        # Ищем вручную
        if 'Total Chapters' in response.text:
            pos = response.text.find('Total Chapters')
            snippet = response.text[pos:pos+150]
            print(f"\nКонтекст 'Total Chapters':")
            print(f"  {snippet}")
            print()
        
        print("=== Debug End ===\n")
        return None
        
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None
    """Получает номер последней главы"""
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None

        # Паттерн: учитывает "23Chapter" без пробела
        chapter_pattern = r'(\d+)\s*Chapters?|Chapter\s*(\d+)'
        matches = re.findall(chapter_pattern, response.text, re.IGNORECASE)

        # Извлекаем все номера глав
        chapter_numbers = []
        for match in matches:
            num = match[0] if match[0] else match[1]
            if num:
                chapter_numbers.append(int(num))

        if chapter_numbers:
            return max(chapter_numbers)
        return None
        
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None


def get_manga_details():
    """Получает информацию о манге"""
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Ошибка получения страницы: {response.status_code}")
            return None
        
        print(f"Статус: {response.status_code}")
        #print(f"Длина контента: {len(response.text)}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлекаем название проекта
        title = soup.find('h1')
        title_text = title.text.strip() if title else "Не найдено"
        print(f"Название: {title_text}")

        # Последняя глава
        latest_chapter = get_latest_chapter()
        if latest_chapter:
            print(f"Последняя глава: {latest_chapter}")
        else:
            print("Последняя глава не найдена") 

        # Обложка
        images = soup.find_all('img')
        #print(f"Найдено изображений: {len(images)}")

        cover_url = None
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            # Пропускаем Logo и иконки
            if 'logo' in src.lower() or 'logo' in alt.lower():
                continue
            if 'icon' in src.lower() or src.startswith('/icons/'):
                continue
            
            # Берём первую подходящую картинку
            if src and ('http' in src or src.startswith('/')):
                # Если относительный путь, делаем абсолютным
                if src.startswith('/') and not src.startswith('//'):
                    cover_url = f"https://media.qiscans.org{src}"
                else:
                    cover_url = src
                print(f"Обложка найдена: {cover_url}")
                break

        return {
            'title': title_text,
            'latest_chapter': latest_chapter,
            'cover_url': cover_url
        }
        
    except requests.RequestException as e:
        print(f"Ошибка при запросе: {e}")
        return None


@client.event
# Событие когда бот запустился
async def on_ready():
    global total_chapters

    print(f"Бот запущен как {client.user}")
    print(f'Канал для уведомлений: {CHANNEL_ID}')
    print("Получение деталей манги...\n")

    # Получаем начальное количество глав
    info = get_manga_details()
    
    if info and info['latest_chapter']:
        total_chapters = info['latest_chapter']
        print(f"\nТекущая глава: {total_chapters}")
        #print(f"Название: {info['title']}")
        #if info['cover_url']:
            #print(f"Обложка: {info['cover_url']}")
    else:
        print("Не удалось получить общее количество глав.")
        return
    
    print("\n" + "="*50)
    print("Мониторинг новых глав... (проверка каждые 10 минут)")
    print("Нажмите Ctrl+C для остановки.")
    print("="*50 + "\n")

    # Запускаем цикл проверки новых глав
    check_new_chapters.start()


@tasks.loop(minutes=10)  # Проверяет новые главы каждые 10 минут
# Автоматическая проверка новых глав
async def check_new_chapters():
    global total_chapters

    import datetime
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"Проверка на новые главы... ({current_time})")

    current_chapter = get_latest_chapter()

    if current_chapter is None:
        print("Не удалось получить количество глав.\n")
        return
    
    if current_chapter > total_chapters:
        # Новая глава!
        new_chapters = current_chapter - total_chapters

        print(f"\n{'='*50}")
        print(f"НОВАЯ ГЛАВА ВЫШЛА!")
        print(f"Номер главы: Chapter {current_chapter}")
        print(f"Вышло новых глав: +{new_chapters}")
        print(f"Ссылка: {url}/chapter-{current_chapter}")
        print(f"{'='*50}\n")

        # Отправляем сообщение в Discord
        channel = client.get_channel(CHANNEL_ID)

        if channel:
            info = get_manga_details()

            # Создаем embed сообщение
            embed = discord.Embed(
                title="Новая глава вышла!",
                description=f"**{info['title'] if info else 'The Strongest Outcast'}**",
                color=discord.Color.green(),
                url=f"{url}/chapter-{current_chapter}"
            )

            embed.add_field(
                name="Глава",
                value=f"Chapter {current_chapter}",
                inline=True
            )

            embed.add_field(
                name="Новых глав",
                value=f"+{new_chapters}",
                inline=True
            )

            if info and info['cover_url']:
                embed.set_thumbnail(url=info['cover_url'])

            embed.set_footer(text="qiscans.org - Manga Tracker Bot")

            await channel.send(embed=embed)
            print("Сообщение отправлено в Discord!\n")
        else:
            print("Не удалось найти канал для отправки сообщения.\n")

        # Обновляем общее количество глав
        total_chapters = current_chapter
    else:
        print(f"Обновлений нет (текущая глава: {total_chapters})\n")


# Запускаем основной процесс
if __name__ == "__main__":
    if not TOKEN:
        print("Ошибка: DISCORD_TOKEN не установлен в .env файле.")
    elif not CHANNEL_ID:
        print("Ошибка: CHANNEL_ID не установлен в .env файле.")
    else:
        print("Запуск Discord бота...\n")
        try:
            client.run(TOKEN)
        except KeyboardInterrupt:
            print("\n\nМониторинг остановлен пользователем.")