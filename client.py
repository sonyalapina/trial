import os
import time
import fcntl
from config import *


class Server:
    def __init__(self):
        self.shared_file_path = SHARED_FILE_PATH
        self.just_wrote = False  # Флаг, что мы только что записали ответ
        self.create_shared_file()

    def create_shared_file(self):
        try:
            with open(self.shared_file_path, 'w') as f:
                pass
            os.chmod(self.shared_file_path, 0o666)
            print(f"Создан общий файл: {self.shared_file_path}")
        except Exception as e:
            print(f"Ошибка при создании файла: {e}")
            raise

    def lock_file(self, fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            return True
        except:
            return False

    def unlock_file(self, fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except:
            pass

    def read_client_message(self):
        """Читаем сообщение, но игнорируем если это наш только что записанный ответ"""
        try:
            fd = os.open(self.shared_file_path, os.O_RDWR)

            if not self.lock_file(fd):
                os.close(fd)
                return None

            try:
                file_size = os.fstat(fd).st_size
                if file_size == 0:
                    return None

                os.lseek(fd, 0, os.SEEK_SET)
                content = os.read(fd, file_size).decode(ENCODING).strip()

                if content:
                    # Если мы только что записали ответ - игнорируем его
                    if self.just_wrote:
                        print(f"[Сервер] Игнорирую только что записанный ответ: '{content}'")
                        # Очищаем файл и сбрасываем флаг
                        os.ftruncate(fd, 0)
                        os.lseek(fd, 0, os.SEEK_SET)
                        os.fsync(fd)
                        self.just_wrote = False
                        return None
                    
                    # Это настоящее сообщение от клиента
                    print(f"[Сервер] Найдено сообщение от клиента: '{content}'")
                    os.ftruncate(fd, 0)
                    os.lseek(fd, 0, os.SEEK_SET)
                    os.fsync(fd)
                    return content

            finally:
                self.unlock_file(fd)
                os.close(fd)

            return None

        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return None

    def write_response(self, response):
        try:
            fd = os.open(self.shared_file_path, os.O_RDWR | os.O_CREAT)

            if not self.lock_file(fd):
                os.close(fd)
                return False

            try:
                # Ждем, чтобы клиент успел отпустить блокировку
                time.sleep(0.05)

                # Устанавливаем флаг, что мы собираемся записать ответ
                self.just_wrote = True
                
                # Записываем ответ
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                os.fsync(fd)

                os.write(fd, response.encode(ENCODING))
                os.fsync(fd)
                
                print(f"[Сервер] Записан ответ в файл: '{response}'")

                return True

            finally:
                self.unlock_file(fd)
                os.close(fd)

        except Exception as e:
            print(f"Ошибка при записи в файл: {e}")
            self.just_wrote = False
            return False

    def process_message(self, message):
        if not message:
            return "Ошибка: пустое сообщение"
        message = message.strip().lower()
        if message == "ping":
            return "pong"
        return "Ошибка: отправьте 'ping'"

    def run(self):
        print(" ")
        print("СЕРВЕР ЗАПУЩЕН")
        print(" ")
        print("Сервер ждет сообщения от клиента...\n")

        try:
            while True:
                message = None

                while message is None:
                    message = self.read_client_message()
                    if message is None:
                        time.sleep(POLL_INTERVAL)

                print(f"[Сервер] Обрабатываю сообщение: '{message}'")

                response = self.process_message(message)
                print(f"[Сервер] Готовлю ответ: '{response}'")

                if self.write_response(response):
                    print("[Сервер] Ответ успешно отправлен")
                else:
                    print("[Сервер] Ошибка отправки ответа")
                    
                # Даем время клиенту прочитать ответ
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n[Сервер] Остановка")
        finally:
            self.cleanup()

    def cleanup(self):
        try:
            if os.path.exists(self.shared_file_path):
                os.remove(self.shared_file_path)
                print(f"[Сервер] Файл удален: {self.shared_file_path}")
        except:
            pass


if __name__ == "__main__":
    server = Server()
    server.run()
