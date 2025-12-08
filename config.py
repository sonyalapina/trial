import os

# Кодировка файла
ENCODING = 'utf-8'

# Интервал опроса файла (секунды)
POLL_INTERVAL = 0.1

# Таймаут ожидания (секунды)
READ_TIMEOUT = 5

# Путь к общему файлу
SHARED_FILE_PATH = os.path.join(os.path.dirname(file), 'shared_file.txt')
