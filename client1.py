#!/usr/bin/env python3
import os
import sys
import errno

def client():
    """Простой клиент для ping-pong"""
    print("=== Клиент PING-PONG ===")
    
    # Имена FIFO файлов
    ping_fifo = "/tmp/ping_fifo"
    pong_fifo = "/tmp/pong_fifo"
    
    # Проверяем, запущен ли сервер
    if not os.path.exists(ping_fifo) or not os.path.exists(pong_fifo):
        print("Ошибка: Сервер не запущен!")
        print("Запустите сначала сервер: python3 server.py")
        return 1
    
    print("\nВведите 'ping' для отправки запроса")
    print("Или 'exit' для выхода\n")
    
    while True:
        # Запрашиваем ввод от пользователя
        user_input = input("Введите сообщение: ").strip()
        
        if user_input.lower() == "exit":
            print("Завершение работы клиента...")
            break
        
        if user_input != "ping":
            print("Ошибка: можно отправить только 'ping'")
            print("Попробуйте снова\n")
            continue
        
        try:
            # 1. Открываем FIFO для отправки запроса серверу
            print("\nОтправка запроса серверу...")
            ping_fd = os.open(ping_fifo, os.O_WRONLY)
            print(f"Открыт файловый дескриптор для записи: {ping_fd}")
            
            # 2. Отправляем "ping"
            message = "ping"
            os.write(ping_fd, message.encode('utf-8'))
            print(f"Отправлено сообщение: '{message}'")
            
            # 3. Закрываем дескриптор записи
            os.close(ping_fd)
            
            # 4. Открываем FIFO для получения ответа от сервера
            print("Ожидание ответа от сервера...")
            pong_fd = os.open(pong_fifo, os.O_RDONLY)
            print(f"Открыт файловый дескриптор для чтения: {pong_fd}")
            
            # 5. Читаем ответ от сервера
            data = os.read(pong_fd, 1024)
            response = data.decode('utf-8').strip()
            print(f"Получен ответ от сервера: '{response}'")
            
            # 6. Закрываем дескриптор чтения
            os.close(pong_fd)
            
            if response == "pong":
                print("✓ Успешный обмен сообщениями!")
            else:
                print(f"✗ Неожиданный ответ: '{response}'")
            
            print("\n" + "="*40 + "\n")
            
        except OSError as e:
            if e.errno == errno.EPIPE:
                print("Ошибка: Сервер недоступен")
                break
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
