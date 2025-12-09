#!/usr/bin/env python3

import os
import sys
import errno
import time
import uuid

def server(server_id=None):
    # Генерируем уникальный ID сервера, если не задан
    if server_id is None:
        server_id = str(uuid.uuid4())[:8]
    
    # Общий файл для общения с уникальными ID сервера
    shared_file = f"/tmp/shared_communication_{server_id}.txt"
    
    # Файл для хранения информации о клиентах
    clients_file = f"/tmp/clients_info_{server_id}.txt"
    
    # Инициализация счётчика клиентов
    try:
        with open(clients_file, 'w') as f:
            f.write("0")
    except:
        pass
    
    print(f"Сервер {server_id} запущен")
    print(f"Файл общения: {shared_file}")
    print("Для подключения клиента используйте команду:")
    print(f"python client.py {server_id}")
    print()
    
    try:
        # Создание файла
        with open(shared_file, 'w') as f:
            pass
        print(f"Файл {shared_file} готов")

        print("Ожидание запроса от клиента...\n")
        
        while True:
            try:
                fd = os.open(shared_file, os.O_RDWR)
                
                try:
                    # Блокировка файла
                    os.lockf(fd, os.F_LOCK, 0)
                    
                    # Чтение данных
                    os.lseek(fd, 0, os.SEEK_SET)
                    data = os.read(fd, 1024)
                    
                    if data:
                        message_data = data.decode('utf-8').strip()
                        
                        # Парсим сообщение: номер_клиента:сообщение
                        if ':' in message_data:
                            client_num, message = message_data.split(':', 1)
                            client_num = client_num.strip()
                            message = message.strip()
                            
                            print(f"Сервер {server_id}: Получено сообщение от клиента №{client_num}: {message}")
                            
                            # Очистка файла
                            time.sleep(1)
                            os.ftruncate(fd, 0)

                            if message.lower() == "ping":
                                response = f"Клиент №{client_num}: pong от сервера {server_id}"
                                # Запись ответа в файл
                                os.lseek(fd, 0, os.SEEK_SET)
                                os.write(fd, response.encode('utf-8'))
                                print(f"Сервер {server_id}: Отправлен ответ клиенту №{client_num}")
                                
                                # Сброс буферов на диск
                                os.fsync(fd)                            
                            else:
                                # Вывод ошибки в терминал
                                error_msg = f"Сервер {server_id}: Клиент №{client_num}: Ошибка: неверный запрос"
                                print(error_msg)
                                os.lseek(fd, 0, os.SEEK_SET)
                                os.write(fd, b" ")
                                os.fsync(fd)
                        else:
                            # Формат неверный
                            print(f"Сервер {server_id}: Получено некорректное сообщение: {message_data}")
                            os.lseek(fd, 0, os.SEEK_SET)
                            os.write(fd, b" ")
                            os.fsync(fd)
                        
                        print("\n")
                    
                    os.lockf(fd, os.F_ULOCK, 0)
                    
                except Exception as e:
                    # Освобождаем блокировку при ошибке
                    try:
                        os.lockf(fd, os.F_ULOCK, 0)
                    except:
                        pass
                    raise
            
                os.close(fd)
                time.sleep(0.1)
                    
            except KeyboardInterrupt:
                print(f"\nСервер {server_id} завершает работу...")
                
                # Сообщаем клиентам о завершении работы
                shutdown_message = "SERVER_SHUTDOWN"
                try:
                    fd = os.open(shared_file, os.O_WRONLY)
                    os.lockf(fd, os.F_LOCK, 0)
                    os.lseek(fd, 0, os.SEEK_SET)
                    os.write(fd, shutdown_message.encode('utf-8'))
                    os.fsync(fd)
                    os.lockf(fd, os.F_ULOCK, 0)
                    os.close(fd)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения о завершении работы: {e}")

                # Удаляем общие файлы
                if os.path.exists(shared_file):
                    os.unlink(shared_file)
                    print(f"Файл {shared_file} удалён")
                
                if os.path.exists(clients_file):
                    os.unlink(clients_file)
                    print(f"Файл {clients_file} удалён")
                
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)
                continue
                
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        return 0

if __name__ == "__main__":
    # Возможность задать ID сервера через аргументы
    server_id = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(server(server_id))
