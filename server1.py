#!/usr/bin/env python3

import os
import sys
import errno
import time
import uuid
import signal

def server(server_id=None):
    # Генерируем уникальный ID сервера если не указан
    if server_id is None:
        server_id = str(uuid.uuid4())[:8]
    
    # Имя общего файла для общения с уникальным ID сервера
    shared_file = f"/tmp/shared_communication_{server_id}.txt"
    
    # Файл для хранения информации о клиентах
    clients_file = f"/tmp/clients_info_{server_id}.txt"
    
    # Флаг для корректного завершения
    is_shutting_down = False
    
    # Функция для обработки сигналов завершения
    def shutdown_handler(signum, frame):
        nonlocal is_shutting_down
        if not is_shutting_down:
            is_shutting_down = True
            print(f"\nСервер {server_id} завершает работу...")
            
            # Оповещаем всех клиентов о завершении работы сервера
            try:
                if os.path.exists(shared_file):
                    fd = os.open(shared_file, os.O_RDWR)
                    try:
                        # Блокируем файл
                        os.lockf(fd, os.F_LOCK, 0)
                        
                        # Записываем сообщение о завершении сервера
                        shutdown_msg = "SERVER_SHUTDOWN"
                        os.lseek(fd, 0, os.SEEK_SET)
                        os.write(fd, shutdown_msg.encode('utf-8'))
                        os.ftruncate(fd, len(shutdown_msg))
                        
                        # Сбрасываем буферы на диск
                        os.fsync(fd)
                        
                        os.lockf(fd, os.F_ULOCK, 0)
                    except Exception as e:
                        try:
                            os.lockf(fd, os.F_ULOCK, 0)
                        except:
                            pass
                    finally:
                        os.close(fd)
            except Exception as e:
                print(f"Ошибка при оповещении клиентов: {e}")
            
            # Даем время клиентам получить сообщение
            time.sleep(1)
            
            # Удаляем файлы
            if os.path.exists(shared_file):
                os.unlink(shared_file)
                print(f"Файл {shared_file} удален")
            
            if os.path.exists(clients_file):
                os.unlink(clients_file)
                print(f"Файл {clients_file} удален")
            
            sys.exit(0)
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Инициализируем счетчик клиентов
    try:
        with open(clients_file, 'w') as f:
            f.write("0")
    except:
        pass
    
    print(f"Сервер {server_id} запущен")
    print(f"Файл общения: {shared_file}")
    print("Для подключения клиента используйте команду:")
    print(f"python client.py {server_id}")
    print("Для завершения сервера нажмите Ctrl+C")
    print()
    
    try:
        # Создаем файл
        with open(shared_file, 'w') as f:
            pass
        print(f"Файл {shared_file} готов")

        print("Ожидание запроса от клиента...\n")
        
        while True:
            try:
                fd = os.open(shared_file, os.O_RDWR)
                
                try:
                    # Блокируем файл
                    os.lockf(fd, os.F_LOCK, 0)
                    
                    # Перемещаем указатель в начало
                    os.lseek(fd, 0, os.SEEK_SET)
                    
                    # Читаем данные
                    data = os.read(fd, 1024)
                    
                    if data:
                        message_data = data.decode('utf-8').strip()
                        
                        # Если клиент отправил сообщение о завершении
                        if message_data == "SERVER_SHUTDOWN":
                            # Это должно быть только от сервера при shutdown
                            os.lseek(fd, 0, os.SEEK_SET)
                            os.write(fd, b" ")
                            os.fsync(fd)
                        # Разбираем сообщение: номер_клиента:сообщение
                        elif ':' in message_data:
                            client_num, message = message_data.split(':', 1)
                            client_num = client_num.strip()
                            message = message.strip()
                            
                            print(f"Сервер {server_id}: Получено сообщение от клиента №{client_num}: {message}")
                            
                            # Очищаем файл
                            time.sleep(1)
                            os.ftruncate(fd, 0)

                            if message.lower() == "ping":
                                response = f"Клиент №{client_num}: pong от сервера {server_id}"
                                # Записываем ответ в файл
                                os.lseek(fd, 0, os.SEEK_SET)
                                os.write(fd, response.encode('utf-8'))
                                print(f"Сервер {server_id}: Отправлен ответ клиенту №{client_num}")
                                
                                # Сбрасываем буферы на диск
                                os.fsync(fd)                            
                            else:
                                # Выводим ошибку в терминал
                                error_msg = f"Сервер {server_id}: Клиент №{client_num}: Ошибка: неверный запрос"
                                print(error_msg)
                                os.lseek(fd, 0, os.SEEK_SET)
                                os.write(fd, b" ")
                                os.fsync(fd)
                        else:
                            # Если формат неверный
                            print(f"Сервер {server_id}: Получено некорректное сообщение: {message_data}")
                            os.lseek(fd, 0, os.SEEK_SET)
                            os.write(fd, b" ")
                            os.fsync(fd)
                        
                        print("\n")
                    
                    os.lockf(fd, os.F_ULOCK, 0)
                    
                except Exception as e:
                    # При ошибке снимаем блокировку
                    try:
                        os.lockf(fd, os.F_ULOCK, 0)
                    except:
                        pass
                    raise
            
                os.close(fd)
                time.sleep(0.1)
                    
            except KeyboardInterrupt:
                # Обработчик сигнала уже обработает это
                continue
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)
                continue
                
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Позволяем указать ID сервера как аргумент командной строки
    server_id = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(server(server_id))
