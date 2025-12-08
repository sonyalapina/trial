#!/usr/bin/env python3
import os
import time
import sys
import errno

def client():
    # Имя общего файла для общения
    shared_file = "/tmp/shared_communication.txt"
    
    # Проверяем, запущен ли сервер (существует ли файл)
    if not os.path.exists(shared_file):
        print("Запустите сначала сервер")
        return 1
    
    print("\nВведите 'ping' для запроса")
    print("Или 'exit' для выхода\n")
    
    while True:
        # Запрашиваем ввод от пользователя
        user_input = input("Введите сообщение: ").strip()
        
        if user_input.lower() == "exit":
            print("Завершение работы клиента...")
            break
        
        try:
            print(f"\nОтправка запроса '{user_input}' серверу...")
            
            # 1. Открываем файл для записи с блокировкой
            fd = os.open(shared_file, os.O_RDWR)
            
            # 2. Блокируем файл для эксклюзивного доступа
            os.lockf(fd, os.F_LOCK, 0)
            
            # 3. Записываем запрос в файл
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, user_input.encode('utf-8'))
            
            # 4. Сбрасываем буферы на диск
            os.fsync(fd)
            print(f"Запрос записан в файл")
            
            # 5. Снимаем блокировку
            os.lockf(fd, os.F_ULOCK, 0)
            
            # 6. Закрываем файл
            os.close(fd)
            
            # 7. Ждем ответа от сервера
            print("Ожидание ответа от сервера...")
            
            response_received = False
            timeout = 5  # Таймаут 5 секунд
            start_time = time.time()
            
            while not response_received and (time.time() - start_time) < timeout:
                try:
                    # Открываем файл для чтения
                    fd = os.open(shared_file, os.O_RDWR)
                    
                    # Блокируем для чтения
                    os.lockf(fd, os.F_LOCK, 0)
                    
                    # Читаем ответ
                    os.lseek(fd, 0, os.SEEK_SET)
                    data = os.read(fd, 1024)
                    
                    if data:
                        response = data.decode('utf-8').strip()
                        
                        # Проверяем, это ответ на наш запрос?
                        # (простая проверка - ответ не должен быть равен нашему запросу)
                        if response != user_input:
                            print(f"Получен ответ от сервера: '{response}'")
                            response_received = True
                            
                            # Очищаем файл для следующего запроса
                            os.ftruncate(fd, 0)
                    
                    # Снимаем блокировку
                    os.lockf(fd, os.F_ULOCK, 0)
                    os.close(fd)
                    
                except Exception as e:
                    try:
                        os.lockf(fd, os.F_ULOCK, 0)
                        os.close(fd)
                    except:
                        pass
                
                if not response_received:
                    time.sleep(0.1)  # Короткая пауза
            
            if not response_received:
                print("Таймаут: сервер не ответил")
            
            print("\n" + "="*40 + "\n")
            
        except OSError as e:
            if e.errno == errno.EACCES:
                print("Ошибка доступа к файлу")
            else:
                print(f"Ошибка ввода-вывода: {e}")
            break
        except KeyboardInterrupt:
            print("\nЗавершение работы...")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            break
    
    return 0

if __name__ == "__main__":
    sys.exit(client())
