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
    
    # Файл для хранения счетчика клиентов
    counter_file = f"/tmp/client_counter_{server_id}.txt"
    
    # Получаем номер клиента
    client_number = 1
    try:
        fd = os.open(counter_file, os.O_RDWR | os.O_CREAT)
        os.lockf(fd, os.F_LOCK, 0)
        
        try:
            data = os.read(fd, 16)
            if data:
                client_number = int(data.decode('utf-8').strip()) + 1
        except:
            pass
            
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, str(client_number).encode('utf-8'))
        os.ftruncate(fd, len(str(client_number)))
        
        os.lockf(fd, os.F_ULOCK, 0)
        os.close(fd)
    except:
        pass  # Если не удалось получить номер, используем 1
    
    print(f"\nКлиент #{client_number} подключается к серверу {server_id}")
    print("Введите запрос или 'exit' для выхода")
    print("Доступные команды: ping, имя, test\n")
    
    try:    
        while True:
            user_input = input(f"Клиент #{client_number}> ").strip()
            
            if user_input.lower() == "exit":
                print("Завершение работы клиента...")
                break

            if not user_input:                
                print(f"Клиент #{client_number}> Ошибка: запрос не может быть пустым")
                continue
            
            try:            
                # Открываем файл для записи с блокировкой
                fd = os.open(shared_file, os.O_RDWR)            
                os.lockf(fd, os.F_LOCK, 0)
                
                # Записываем запрос в файл с номером клиента
                formatted_request = f"#{client_number}:{user_input}"
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, formatted_request.encode('utf-8'))
                
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
                            
                            # Проверяем, содержит ли ответ наш номер клиента
                            expected_prefix = f"#{client_number}:"
                            if response.startswith(expected_prefix):
                                response_content = response[len(expected_prefix):]
                                if response_content.strip() == " ":
                                    print(f"Клиент #{client_number}> Ошибка: неверный запрос")
                                else:
                                    print(f"Клиент #{client_number}> Ответ от сервера: {response_content.strip()}")
                                response_received = True
                            
                            # Очищаем файл если ответ наш
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
                    print(f"Клиент #{client_number}> Таймаут: сервер не ответил")
                
                print("")
           
            except OSError as e:
                if e.errno == errno.EACCES:
                    print(f"Клиент #{client_number}> Ошибка доступа к файлу")
                break
            except Exception as e:
                print(f"Клиент #{client_number}> Неожиданная ошибка: {e}")
                break
    
    except KeyboardInterrupt:
        print(f"\nКлиент #{client_number} завершает работу...")
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <server_id>")
        print("Пример: python client.py server1")
        sys.exit(1)
    
    server_id = sys.argv[1]
    sys.exit(client(server_id))
