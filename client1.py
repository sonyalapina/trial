#!/usr/bin/env python3
import os
import time
import sys
import errno

def client(server_id):
    # Используем тот же файл, что и сервер
    shared_file = f"/tmp/shared_communication_{server_id}.txt"
    
    if not os.path.exists(shared_file):
        print(f"Сервер с ID '{server_id}' не запущен или файл не найден")
        print("Запустите сервер с командой: python server.py [server_id]")
        return 1
    
    print(f"\nПодключение к серверу {server_id}")
    print("Введите запрос или 'exit' для выхода\n")
    
    try:    
        while True:
            user_input = input("Введите сообщение: ").strip()
            
            if user_input.lower() == "exit":
                print("Завершение работы клиента...")
                break

            if not user_input:                
                print("Ошибка: запрос не может быть пустым\n")
                continue
            
            try:            
                # Открываем файл для записи с блокировкой
                fd = os.open(shared_file, os.O_RDWR)            
                os.lockf(fd, os.F_LOCK, 0)
                
                # Записываем запрос в файл
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, user_input.encode('utf-8'))
                
                # Сбрасываем на диск
                os.fsync(fd)
                
                # Снимаем блокировку
                os.lockf(fd, os.F_ULOCK, 0)
                os.close(fd)
                
                response_received = False
                timeout = 5
                start_time = time.time()
                
                while not response_received and (time.time() - start_time) < timeout:
                    try:
                        # Открываем для чтения
                        fd = os.open(shared_file, os.O_RDWR)
                        
                        # Блокируем для чтения
                        os.lockf(fd, os.F_LOCK, 0)
                        
                        # Читаем ответ
                        os.lseek(fd, 0, os.SEEK_SET)
                        data = os.read(fd, 1024)
                        
                        if data:
                            response = data.decode('utf-8')
                            
                            if response == " ":
                                print("Ошибка: неверный запрос")
                                response_received = True
                            else:
                                response_stripped = response.strip()
                                if response_stripped != user_input:
                                    print(f"Получен ответ от сервера {server_id}: {response_stripped}")
                                    response_received = True
                            
                            # Очищаем файл
                            if response_received:
                                os.ftruncate(fd, 0)

                        os.lockf(fd, os.F_ULOCK, 0)
                        os.close(fd)                        
                   
                    except Exception as e:
                        try:
                            if 'fd' in locals():
                                os.lockf(fd, os.F_ULOCK, 0)
                                os.close(fd)
                        except:
                            pass
                        continue
                    
                    if not response_received:
                        time.sleep(0.1)
                
                if not response_received:
                    print("Таймаут: сервер не ответил")
                
                print("\n")
           
            except OSError as e:
                if e.errno == errno.EACCES:
                    print("Ошибка доступа к файлу")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break
    
    except KeyboardInterrupt:
        print("\nЗавершение работы клиента...")
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <server_id>")
        print("Пример: python client.py server1")
        sys.exit(1)
    
    server_id = sys.argv[1]
    sys.exit(client(server_id))
