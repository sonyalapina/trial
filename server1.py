#!/usr/bin/env python3
import os
import sys
import errno

def server():
    
    
    # Создаем именованные каналы (FIFO)
    ping_fifo = "/tmp/ping_fifo"
    pong_fifo = "/tmp/pong_fifo"
    
    try:
        # Создаем FIFO если не существуют
        try:
            os.mkfifo(ping_fifo)
            print(f"Создан FIFO для ping: {ping_fifo}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        
        try:
            os.mkfifo(pong_fifo)
            print(f"Создан FIFO для pong: {pong_fifo}")
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
        
        print("\nСервер ожидает сообщение 'ping'...")
        print("Для завершения нажмите Ctrl+C\n")
        
        while True:
            try:
                # 1. Открываем FIFO для чтения от клиента (блокирующий режим)
                print("Ожидание запроса от клиента...")
                ping_fd = os.open(ping_fifo, os.O_RDONLY)
                
                
                # 2. Читаем сообщение от клиента
                data = os.read(ping_fd, 1024)
                message = data.decode('utf-8').strip()
                print(f"Получено сообщение: '{message}'")
                
                # 3. Закрываем дескриптор чтения
                os.close(ping_fd)
                
                # 4. Проверяем сообщение
                if message.lower() == "ping":
                    
                    
                    # 5. Открываем FIFO для записи ответа клиенту
                    pong_fd = os.open(pong_fifo, os.O_WRONLY)
                    
                    
                    # 6. Отправляем ответ "pong"
                    response = "pong"
                    os.write(pong_fd, response.encode('utf-8'))
                    print(f"Отправлен ответ: '{response}'")
                    
                    # 7. Закрываем дескриптор записи
                    os.close(pong_fd)
                    
                    print("=" * 40 + "\n")
                else:
                    print(f"Ошибка: неверный запрос")
                    print("=" * 40 + "\n")
                    
            except KeyboardInterrupt:
                print("\nСервер завершает работу...")
                break
            except OSError as e:
                print(f"Ошибка ввода-вывода: {e}")
                break
                
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return 1
    finally:
        # Удаляем FIFO файлы при завершении
        try:
            os.unlink(ping_fifo)
            os.unlink(pong_fifo)
            print("FIFO файлы удалены")
        except:
            pass
    
    return 0

if __name__ == "__main__":
    sys.exit(server())
