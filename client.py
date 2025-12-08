import os
import time
import fcntl
ENCODING = 'utf-8'

# Интервал опроса файла (секунды)
POLL_INTERVAL = 0.1

# Таймаут ожидания (секунды)
READ_TIMEOUT = 5

# Путь к общему файлу
SHARED_FILE_PATH = os.path.join(os.path.dirname(__file__), 'shared_file.txt')


class Client:
    def __init__(self):
        self.shared_file_path = SHARED_FILE_PATH
        self.last_sent_message = None  # Запоминаем, что отправили

    def check_file_exists(self):
        if not os.path.exists(self.shared_file_path):
            print("Файл не найден, сначала запустите сервер!")
            return False
        return True

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

    def send_message(self, message):
        if not self.check_file_exists():
            return False, "Файл не существует"

        try:
            fd = os.open(self.shared_file_path, os.O_RDWR)
            start_time = time.time()

            while time.time() - start_time < READ_TIMEOUT:
                if self.lock_file(fd):
                    break
                time.sleep(0.01)
            else:
                os.close(fd)
                return False, "Не удалось заблокировать файл"

            try:
                # ИСПРАВЛЕНИЕ: просто очищаем файл, НЕ читаем его содержимое
                # Очищаем файл перед записью нового сообщения
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                os.fsync(fd)

                # Записываем сообщение
                os.write(fd, message.encode(ENCODING))
                os.fsync(fd)

                self.last_sent_message = message  # Запоминаем, что отправили
                print(f"[Клиент] Отправлено: '{message}'")
                return True, None

            finally:
                self.unlock_file(fd)
                os.close(fd)

        except Exception as e:
            return False, f"Ошибка отправки: {e}"

    def wait_for_response(self):
        if not self.check_file_exists():
            return False, None, "Файл не существует"

        try:
            start_time = time.time()
            last_content = None

            while time.time() - start_time < READ_TIMEOUT:
                fd = os.open(self.shared_file_path, os.O_RDONLY)
                
                try:
                    # Пробуем получить блокировку для чтения
                    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                    
                    file_size = os.fstat(fd).st_size
                    if file_size > 0:
                        os.lseek(fd, 0, os.SEEK_SET)
                        response = os.read(fd, file_size).decode(ENCODING).strip()
                        
                        # ИСПРАВЛЕНИЕ: проверяем, что это не наше же сообщение
                        if response and response != self.last_sent_message:
                            print(f"[Клиент] Получен ответ: '{response}'")
                            return True, response, None
                            
                except BlockingIOError:
                    # Файл заблокирован - сервер работает
                    pass
                finally:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                    except:
                        pass
                    os.close(fd)
                
                time.sleep(POLL_INTERVAL)

            return False, None, "Таймаут ожидания ответа"

        except Exception as e:
            return False, None, f"Ошибка получения ответа: {e}"

    def run(self):
        print(" ")
        print("КЛИЕНТ ЗАПУЩЕН")
        print(" ")
        print("Введите сообщение для отправки серверу")
        print("Только 'ping' получит ответ 'pong'")
        print("Любое другое сообщение получит ошибку")

        while True:
            try:
                print("\n[Клиент] Введите сообщение:")
                user_input = input("> ").strip()

                if user_input.lower() == "exit":
                    print("[Клиент] Выход")
                    break

                if not user_input:
                    print("[Клиент] Пустое сообщение, попробуйте снова")
                    continue

                success, error = self.send_message(user_input)
                if not success:
                    print(f"[Клиент] Ошибка: {error}")
                    continue

                print("[Клиент] Ожидание ответа от сервера...")

                success, response, error = self.wait_for_response()
                if not success:
                    print(f"[Клиент] Ошибка: {error}")
                    continue

                if response == "pong":
                    print(f"[Клиент] Успех! Получен правильный ответ: {response}")
                elif response.startswith("Ошибка"):
                    print(f"[Клиент] Сервер вернул ошибку: {response}")
                else:
                    print(f"[Клиент] Ответ сервера: '{response}'")

            except KeyboardInterrupt:
                print("\n[Клиент] Выход")
                break
            except Exception as e:
                print(f"[Клиент] Ошибка: {e}")


if __name__ == "__main__":
    client = Client()
    client.run()
