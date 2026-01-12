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