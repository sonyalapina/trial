import os
import time
import fcntl
from config import *

class Server:
    def __init__(self):
        self.shared_file_path = SHARED_FILE_PATH
        self.just_wrote_response = False  # ДОБАВЛЕНО: флаг, что мы только что записали ответ
        self.create_shared_file()
        
    def create_shared_file(self):
        try:
            # создаем пустой файл
            with open(self.shared_file_path, 'w') as f:
                pass
            
            # права на чтение и запись всем
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
        try:
            fd = os.open(self.shared_file_path, os.O_RDWR)
            
            if not self.lock_file(fd):
                os.close(fd)
                return None
            
            try:
                # проверяем размер файла
                file_size = os.fstat(fd).st_size
                if file_size == 0:
                    return None
                
                # читаем с начала файла
                os.lseek(fd, 0, os.SEEK_SET)
                content = os.read(fd, file_size).decode(ENCODING)
                
                if content:
                    content = content.strip()
                    
                    # ДОБАВЛЕНО: если мы только что записали ответ, игнорируем его
                    if self.just_wrote_response:
                        self.just_wrote_response = False
                        # очищаем файл (это наш же ответ)
                        os.ftruncate(fd, 0)
                        os.lseek(fd, 0, os.SEEK_SET)
                        os.fsync(fd)
                        return None
                    
                    # очищаем файл ПОСЛЕ чтения
                    os.ftruncate(fd, 0)
                    os.lseek(fd, 0, os.SEEK_SET)
                    os.fsync(fd)  # Важно: сбрасываем изменения на диск
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
                # ЖДЕМ немного, чтобы клиент успел разблокировать файл
                time.sleep(0.05)
                
                # переходим в начало файла и очищаем его
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                os.fsync(fd)  # Гарантируем очистку
                
                # записываем ответ (БЕЗ \n)
                response_bytes = response.encode(ENCODING)
                os.write(fd, response_bytes)
                
                # сбрасываем на диск
                os.fsync(fd)
                
                # ДОБАВЛЕНО: устанавливаем флаг, что мы только что записали ответ
                self.just_wrote_response = True
                
                return True
                
            finally:
                self.unlock_file(fd)
                os.close(fd)
            
        except Exception as e:
            print(f"Ошибка при записи в файл: {e}")
            return False
            
    

    def process_message(self, message):
        if not message:
            return "Ошибка: пустое сообщение"
        
        message = message.strip().lower()
        
        if message == "ping":
            return "pong"
        else:
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
                
                print(f"[Сервер] Получено: '{message}'")
                
                response = self.process_message(message)
                print(f"[Сервер] Отправляю: '{response}'")
                
                if self.write_response(response):
                    print("[Сервер] Ответ отправлен")
                else:
                    print("[Сервер] Ошибка отправки ответа")
                    
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
