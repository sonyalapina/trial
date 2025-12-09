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
    
    # Файл для хранения информации о клиентах
    clients_file = f"/tmp/clients_info_{server_id}.txt"
    client_number = None
    
    # Получаем номер клиента
    try:
        fd = os.open(clients_file, os.O_RDWR | os.O_CREAT)
        os.lockf(fd, os.F_LOCK, 0)
        
        # Читаем текущее количество клиентов
        try:
            data = os.read(fd, 1024)
            if data:
                current_clients = int(data.decode('utf-8').strip())
            else:
                current_clients = 0
        except:
            current_clients = 0
        
        # Увеличиваем счетчик и получаем номер клиента
        client_number = current_clients + 1
        
        # Записываем обновленное количество
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, str(client_number).encode('utf-8'))
        os.ftruncate(fd, len(str(client_number)))
        os.fsync(fd)
        
        os.lockf(fd, os.F_ULOCK, 0)
        os.close(fd)
        
        print(f"\nПодключение к серверу {server_id}")
        print(f"Вы - клиент №{client_number}")
        print("Введите запрос или 'exit' для выхода\n")
        
    except Exception as e:
        print(f"Ошибка при получении номера клиента: {e}")
        return 1
    
    try:    
        while True:
            user_input = input(f"Клиент №{client_number}> ").strip()
            
            if user_input.lower() == "exit":
                print(f"Клиент №{client_number} завершает работу...")
                
                # Уменьшаем счетчик клиентов при выходе
                try:
                    fd = os.open(clients_file, os.O_RDWR)
                    os.lockf(fd, os.F_LOCK, 0)
                    
                    data = os.read(fd, 1024)
                    if data:
                        current_clients = int(data.decode('utf-8').strip())
                        # Не уменьшаем ниже 0
                        if current_clients > 0:
                            new_count = current_clients - 1
                            os.lseek(fd, 0, os.SEEK_SET)
                            os.write(fd, str(new_count).encode('utf-8'))
                            os.ftruncate(fd, len(str(new_count)))
                    
                    os.lockf(fd, os.F_ULOCK, 0)
                    os.close(fd)
                except:
                    pass
                    
                break

            if not user_input:                
                print(f"Клиент №{client_number}: Ошибка: запрос не может быть пустым\n")
                continue
            
            try:            
                # Открываем файл для записи с блокировкой
                fd = os.open(shared_file, os.O_RDWR)            
                os.lockf(fd, os.F_LOCK, 0)
                
                # Записываем запрос в файл с номером клиента
                request_data = f"{client_number}:{user_input}"
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, request_data.encode('utf-8'))
                
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
                                print(f"Клиент №{client_number}: Ошибка: неверный запрос")
                                response_received = True
                            else:
                                # Проверяем, что ответ отличается от нашего запроса
                                if not response.startswith(f"{client_number}:"):
                                    print(f"Клиент №{client_number}: {response}")
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
                    print(f"Клиент №{client_number}: Таймаут: сервер не ответил")
                
                print()
           
            except OSError as e:
                if e.errno == errno.EACCES:
                    print(f"Клиент №{client_number}: Ошибка доступа к файлу")
                break
            except Exception as e:
                print(f"Клиент №{client_number}: Неожиданная ошибка: {e}")
                break
    
    except KeyboardInterrupt:
        print(f"\nКлиент №{client_number} завершает работу...")
        
        # Уменьшаем счетчик клиентов при прерывании
        try:
            fd = os.open(clients_file, os.O_RDWR)
            os.lockf(fd, os.F_LOCK, 0)
            
            data = os.read(fd, 1024)
            if data:
                current_clients = int(data.decode('utf-8').strip())
                if current_clients > 0:
                    new_count = current_clients - 1
                    os.lseek(fd, 0, os.SEEK_SET)
                    os.write(fd, str(new_count).encode('utf-8'))
                    os.ftruncate(fd, len(str(new_count)))
            
            os.lockf(fd, os.F_ULOCK, 0)
            os.close(fd)
        except:
            pass
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <server_id>")
        print("Пример: python client.py server1")
        sys.exit(1)
    
    server_id = sys.argv[1]
    sys.exit(client(server_id))
