#!/usr/bin/env python3
import os
import sys
import time
import errno
import select

def client():
    """Основная функция клиента"""
    # Имена FIFO файлов
    request_fifo = "/tmp/ping_fifo"
    response_fifo = "/tmp/pong_fifo"
    
    try:
        # Проверяем существование FIFO файлов
        if not os.path.exists(request_fifo) or not os.path.exists(response_fifo):
            print("Ошибка: FIFO файлы не существуют. Запустите сервер первым.")
            return 1
        
        print("Клиент запущен")
        print(f"Request FIFO: {request_fifo}")
        print(f"Response FIFO: {response_fifo}")
        print("\nВведите количество запросов для отправки (или 'exit' для выхода):")
        
        while True:
            user_input = input("> ").strip().lower()
            
            if user_input == "exit":
                print("Завершение работы клиента...")
                break
            
            try:
                num_requests = int(user_input)
                if num_requests <= 0:
                    print("Введите положительное число")
                    continue
                    
            except ValueError:
                print("Введите число или 'exit'")
                continue
            
            successful_requests = 0
            failed_requests = 0
            
            for i in range(num_requests):
                try:
                    # ВАЖНО: Создаем ФАЙЛОВЫЕ ДЕСКРИПТОРЫ для каждого запроса
                    # Открываем FIFO для записи запроса (блокирующий режим)
                    # Возвращается файловый дескриптор (например, 4)
                    request_fd = os.open(request_fifo, os.O_WRONLY)
                    print(f"[{i+1}] Файловый дескриптор для записи: {request_fd}")
                    
                    # Открываем FIFO для чтения ответа (неблокирующий режим)
                    # Возвращается другой файловый дескриптор (например, 5)
                    response_fd = os.open(response_fifo, os.O_RDONLY | os.O_NONBLOCK)
                    print(f"[{i+1}] Файловый дескриптор для чтения: {response_fd}")
                    
                    # Отправляем запрос через файловый дескриптор
                    message = "ping"
                    print(f"[{i+1}] Отправка запроса: '{message}'")
                    
                    try:
                        # os.write() использует файловый дескриптор request_fd
                        os.write(request_fd, message.encode('utf-8'))
                    except OSError as e:
                        if e.errno == errno.EPIPE:
                            print(f"[{i+1}] Ошибка: Сервер не доступен")
                            failed_requests += 1
                            os.close(request_fd)  # Закрываем дескрипторы
                            os.close(response_fd)
                            continue
                        else:
                            raise
                    
                    # ВАЖНО: Закрываем дескриптор записи
                    # Это дает сигнал серверу, что запрос завершен
                    os.close(request_fd)
                    
                    # Ожидаем ответ через файловый дескриптор response_fd
                    poll = select.poll()
                    poll.register(response_fd, select.POLLIN)  # Отслеживаем дескриптор
                    
                    timeout = 5000  # 5 секунд в миллисекундах
                    response_received = False
                    
                    start_time = time.time()
                    while time.time() - start_time < 5:  # Таймаут 5 секунд
                        events = poll.poll(100)  # Проверяем каждые 100мс
                        
                        if events:
                            try:
                                # os.read() использует файловый дескриптор response_fd
                                data = os.read(response_fd, 1024)
                                if data:
                                    response = data.decode('utf-8').strip()
                                    if response == "pong":
                                        print(f"[{i+1}] Получен ответ: '{response}'")
                                        successful_requests += 1
                                        response_received = True
                                        break
                                    else:
                                        print(f"[{i+1}] Неожиданный ответ: '{response}'")
                                        failed_requests += 1
                                        response_received = True
                                        break
                            except OSError as e:
                                if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                    print(f"[{i+1}] Ошибка чтения: {e}")
                                    failed_requests += 1
                                    response_received = True
                                    break
                    
                    # ВАЖНО: Закрываем дескриптор ответа
                    os.close(response_fd)
                    
                    if not response_received:
                        print(f"[{i+1}] Таймаут: ответ не получен")
                        failed_requests += 1
                    
                    # Небольшая задержка между запросами
                    if i < num_requests - 1:
                        time.sleep(0.5)
                        
                except OSError as e:
                    print(f"[{i+1}] Ошибка открытия FIFO: {e}")
                    failed_requests += 1
                    continue
                except Exception as e:
                    print(f"[{i+1}] Неожиданная ошибка: {e}")
                    failed_requests += 1
                    continue
            
            print(f"\nРезультат: успешно {successful_requests}/{num_requests}, "
                  f"ошибок: {failed_requests}\n")
            
    except KeyboardInterrupt:
        print("\n\nКлиент завершает работу...")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(client())
