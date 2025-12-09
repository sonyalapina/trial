#!/usr/bin/env python3

import os
import sys
import errno
import time
import uuid

def server(server_id=None):
    # Генерируем уникальный ID сервера если не указан
    if server_id is None:
        server_id = str(uuid.uuid4())[:8]
    
    # Имя общего файла для общения с уникальным ID сервера
    shared_file = f"/tmp/shared_communication_{server_id}.txt"
    
    print(f"Сервер {server_id} запущен")
    print(f"Файл общения: {shared_file}")
    print("Для подключения клиента используйте команду:")
    print(f"python client.py {server_id}")
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
                        message = data.decode('utf-8').strip()
                        print(f"Сервер {server_id}: Получено сообщение: {message}")
                        
                        # Очищаем файл
                        time.sleep(1)
                        os.ftruncate(fd, 0)

                        if message.lower() == "ping":
                            response = f"pong от сервера {server_id}"
                            # Записываем ответ в файл
                            os.lseek(fd, 0, os.SEEK_SET)
                            os.write(fd, response.encode('utf-8'))
                            print(f"Сервер {server_id}: Отправлен ответ: {response}")
                            
                            # Сбрасываем буферы на диск
                            os.fsync(fd)                            
                        else:
                            # Выводим ошибку в терминал
                            error_msg = f"Сервер {server_id}: Ошибка: неверный запрос"
                            print(error_msg)
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
                print(f"\nСервер {server_id} завершает работу...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)
                continue
                
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        # Удаляем файл при завершении
        if os.path.exists(shared_file):
            os.unlink(shared_file)
            print(f"Файл {shared_file} удален")
    
    return 0

if __name__ == "__main__":
    # Позволяем указать ID сервера как аргумент командной строки
    server_id = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(server(server_id))
