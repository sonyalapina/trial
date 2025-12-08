#!/usr/bin/env python3
import os
import sys
import time
import errno
import select
import signal

def handle_signal(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\nСервер завершает работу...")
    sys.exit(0)

def create_fifo(filename):
    """Создает FIFO (именованный канал) если он не существует"""
    try:
        os.mkfifo(filename)
        print(f"Создан FIFO: {filename}")
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def server():
    """Основная функция сервера"""
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Имена FIFO файлов
    request_fifo = "/tmp/ping_fifo"
    response_fifo = "/tmp/pong_fifo"
    
    try:
        # Создаем FIFO файлы
        create_fifo(request_fifo)
        create_fifo(response_fifo)
        
        print("Сервер запущен. Ожидание запросов...")
        print(f"Request FIFO: {request_fifo}")
        print(f"Response FIFO: {response_fifo}")
        print("Нажмите Ctrl+C для завершения работы\n")
        
        # ВАЖНО: Здесь создаются ФАЙЛОВЫЕ ДЕСКРИПТОРЫ!
        # Открываем FIFO для чтения запросов (неблокирующий режим)
        # os.open() возвращает файловый дескриптор (целое число)
        request_fd = os.open(request_fifo, os.O_RDONLY | os.O_NONBLOCK)
        print(f"Открыт файловый дескриптор для чтения: {request_fd}")
        # Это будет число, например: 4, 5, 6 и т.д.
        
        # Открываем FIFO для записи ответов (блокирующий режим)
        response_fd = os.open(response_fifo, os.O_WRONLY)
        print(f"Открыт файловый дескриптор для записи: {response_fd}")
        
        # Используем poll для мониторинга файловых дескрипторов
        poll = select.poll()
        poll.register(request_fd, select.POLLIN)  # Регистрируем дескриптор для отслеживания
        
        request_count = 0
        
        while True:
            try:
                # Ожидаем данные с таймаутом
                events = poll.poll(1000)  # Таймаут 1 секунда
                
                if events:
                    # Читаем запрос от клиента через файловый дескриптор
                    # os.read() использует файловый дескриптор
                    try:
                        data = os.read(request_fd, 1024)  # Чтение через дескриптор request_fd
                        if data:
                            message = data.decode('utf-8').strip()
                            request_count += 1
                            
                            if message == "ping":
                                print(f"[{request_count}] Получен запрос: '{message}'")
                                
                                # Формируем ответ
                                response = "pong"
                                
                                # Отправляем ответ клиенту через файловый дескриптор
                                # os.write() использует файловый дескриптор
                                try:
                                    os.write(response_fd, response.encode('utf-8'))  # Запись через дескриптор response_fd
                                    print(f"[{request_count}] Отправлен ответ: '{response}'")
                                except OSError as e:
                                    if e.errno != errno.EPIPE:
                                        print(f"Ошибка при отправке ответа: {e}")
                                        break
                            else:
                                print(f"[{request_count}] Неизвестный запрос: '{message}'")
                        else:
                            # Клиент закрыл соединение
                            print("Клиент отключился")
                            # Закрываем старый дескриптор
                            os.close(request_fd)
                            # Открываем новый дескриптор для ожидания следующего клиента
                            request_fd = os.open(request_fifo, os.O_RDONLY | os.O_NONBLOCK)
                            poll.register(request_fd, select.POLLIN)
                            
                    except OSError as e:
                        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                            print(f"Ошибка при чтении: {e}")
                            break
                
                # Небольшая пауза для снижения нагрузки на CPU
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\nПрервано пользователем")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break
                
    except OSError as e:
        print(f"Ошибка создания/открытия FIFO: {e}")
        return 1
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        # ВАЖНО: Закрытие файловых дескрипторов - критически важно!
        # Незакрытые дескрипторы могут вызвать утечку ресурсов
        try:
            if 'request_fd' in locals():
                os.close(request_fd)  # Закрываем дескриптор чтения
            if 'response_fd' in locals():
                os.close(response_fd)  # Закрываем дескриптор записи
        except:
            pass
            
        # Удаление FIFO файлов
        try:
            os.unlink(request_fifo)
            os.unlink(response_fifo)
            print(f"\nFIFO файлы удалены")
        except:
            pass
            
        print("Сервер завершил работу")
    
    return 0

if __name__ == "__main__":
    sys.exit(server())
