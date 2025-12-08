import os
import time
import fcntl
from config import *

class Client:
    def __init__(self):
        self.shared_file_path = SHARED_FILE_PATH
        
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
            fd = os.open(self.shared_file_path, os.O_RDWR | os.O_CREAT)
            
            start_time = time.time()
            while time.time() - start_time < READ_TIMEOUT:
                if self.lock_file(fd):
                    break
                time.sleep(0.05)
            else:
                os.close(fd)
                return False, "Не удалось заблокировать файл"
            
            try:
                # УБЕЖДАЕМСЯ, что файл пуст
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                os.fsync(fd)  # Сбрасываем очистку на диск
                
                # записываем сообщение (БЕЗ \n)
                message_bytes = message.encode(ENCODING)
                os.write(fd, message_bytes)
                
                # сбрасываем на диск
                os.fsync(fd)
                
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
            response_received = False
            
            while time.time() - start_time < READ_TIMEOUT:
                # Ждем немного, чтобы сервер успел обработать
                time.sleep(0.2)  # Увеличили задержку
                
                fd = os.open(self.shared_file_path, os.O_RDONLY)
                
                try:
                    # Пробуем получить разделяемую блокировку
                    fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
                except:
                    # Файл заблокирован сервером - это нормально
                    os.close(fd)
                    time.sleep(POLL_INTERVAL)
                    continue
                
                try:
                    # проверяем размер
                    file_size = os.fstat(fd).st_size
                    if file_size > 0:
                        # читаем ответ
                        os.lseek(fd, 0, os.SEEK_SET)
                        response = os.read(fd, file_size).decode(ENCODING).strip()
                        
                        if response and not response_received:
                            response_received = True
                            print(f"[Клиент] Получен ответ: '{response}'")
                            return True, response, None
                
                finally:
                    fcntl.flock(fd, fcntl.LOCK_UN)
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
                
                # Проверяем ответ сервера
                if response == "pong":
                    print(f"[Клиент] Успех! Получен правильный ответ: {response}")
                elif response.startswith("Ошибка"):
                    print(f"[Клиент] Сервер вернул ошибку: {response}")
                else:
                    print(f"[Клиент] Неизвестный ответ сервера: '{response}'")
                    
            except KeyboardInterrupt:
                print("\n[Клиент] Выход")
                break
            except Exception as e:
                print(f"[Клиент] Ошибка: {e}")

if __name__ == "__main__":
    client = Client()
    client.run()
