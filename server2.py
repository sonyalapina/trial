#!/usr/bin/env python3
import os
import sys
import errno
import time

def server():
    # Имя общего файла для общения
    shared_file = "/tmp/shared_communication.txt"
    
    print("\nСервер запущен и ожидает сообщения...")
    print("Для завершения нажмите Ctrl+C\n")
    
    try:
        # Создаем файл если не существует
        if not os.path.exists(shared_file):
            with open(shared_file, 'w') as f:
                pass
            print(f"Создан общий файл: {shared_file}")
        
        # Открываем файл для чтения и записи
        print("Ожидание запроса от клиента...")
        
        while True:
            try:
                # 1. Открываем файл для чтения
                fd = os.open(shared_file, os.O_RDWR)
                
                # 2. Читаем сообщение от клиента
                # Используем блокировку файла
                try:
                    # Пытаемся заблокировать файл
                    os.lockf(fd, os.F_LOCK, 0)
                    
                    # Перемещаем указатель в начало
                    os.lseek(fd, 0, os.SEEK_SET)
                    
                    # Читаем данные
                    data = os.read(fd, 1024)
                    
                    if data:
                        message = data.decode('utf-8').strip()
                        print(f"Получено сообщение: '{message}'")
                        
                        # Очищаем файл
                        os.ftruncate(fd, 0)
                        
                        # 3. Проверяем сообщение и готовим ответ
                        if message.lower() == "ping":
                            response = "pong"
                        else:
                            response = f"error: expected 'ping', got '{message}'"
                        
                        # 4. Записываем ответ в файл
                        os.lseek(fd, 0, os.SEEK_SET)
                        os.write(fd, response.encode('utf-8'))
                        print(f"Отправлен ответ: '{response}'")
                        
                        # 5. Сбрасываем буферы на диск
                        os.fsync(fd)
                        
                        print("=" * 40 + "\n")
                    
                    # Снимаем блокировку
                    os.lockf(fd, os.F_ULOCK, 0)
                    
                except Exception as e:
                    # В случае ошибки снимаем блокировку
                    try:
                        os.lockf(fd, os.F_ULOCK, 0)
                    except:
                        pass
                    raise
                
                # 6. Закрываем файл
                os.close(fd)
                
                # Небольшая пауза чтобы не грузить процессор
                time.sleep(0.1)
                    
            except KeyboardInterrupt:
                print("\nСервер завершает работу...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")
                time.sleep(1)  # Пауза при ошибке
                continue
                
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        # Удаляем файл при завершении (опционально)
        try:
            os.unlink(shared_file)
            print(f"Файл {shared_file} удален")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(server())
