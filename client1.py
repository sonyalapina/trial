#!/usr/bin/env python3
import os
import time
import sys
import errno
import threading

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
    
    # Флаг для завершения работы
    shutdown_event = threading.Event()
    
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
    
    # Функция для фонового мониторинга сервера
    def monitor_server():
        last_check = 0
        check_interval = 0.5
        
        while not shutdown_event.is_set():
            current_time = time.time()
            if current_time - last_check >= check_interval:
                last_check = current_time
                
                # Проверяем наличие файлов сервера
                if not os.path.exists(shared_file) or not os.path.exists(clients_file):
                    shutdown_event.set()
                    print(f"\nСервер отключен")
                    # Завершаем программу
                    os._exit(0)
                    return
                
                # Проверяем, не пришло ли сообщение о завершении сервера
                try:
                    if os.path.exists(shared_file):
                        fd = os.open(shared_file, os.O_RDWR)
                        try:
                            os.lockf(fd, os.F_LOCK, 0)
                            os.lseek(fd, 0, os.SEEK_SET)
                            data = os.read(fd, 1024)
                            
                            if data:
                                # НЕ используем strip() здесь!
                                response = data.decode('utf-8')
                                if response.strip() == "SERVER_SHUTDOWN":
                                    shutdown_event.set()
                                    print(f"\nСервер отключен")
                                    os._exit(0)
                                    return
                            
                            os.lockf(fd, os.F_ULOCK, 0)
                        except:
                            try:
                                os.lockf(fd, os.F_ULOCK, 0)
                            except:
                                pass
                        finally:
                            os.close(fd)
                except:
                    pass
            
            time.sleep(0.1)
    
    # Запускаем фоновый мониторинг
    monitor_thread = threading.Thread(target=monitor_server, daemon=True)
    monitor_thread.start()
    
    try:
        while not shutdown_event.is_set():
            try:
                # Используем обычный input для нормального ввода
                user_input = input("Введите запрос: ").strip()
                
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print("\nЗавершение работы клиента...")
                break
            except Exception as e:
                # Пропускаем ошибки ввода
                continue
            
            if shutdown_event.is_set():
                print(f"\nСервер отключен")
                # Завершаем программу
                os._exit(0)
                return 0
            
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
                print(f"Ошибка: запрос не может быть пустым\n")
                continue
            
            try:
                # Проверяем, не завершился ли сервер перед отправкой
                if shutdown_event.is_set():
                    print(f"\nСервер отключен")
                    os._exit(0)
                    return 0
                
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
                
                while not response_received and not shutdown_event.is_set() and (time.time() - start_time) < timeout:
                    try:
                        # Открываем для чтения
                        fd = os.open(shared_file, os.O_RDWR)
                        
                        # Блокируем для чтения
                        os.lockf(fd, os.F_LOCK, 0)
                        
                        # Читаем ответ
                        os.lseek(fd, 0, os.SEEK_SET)
                        data = os.read(fd, 1024)
                        
                        if data:
                            # НЕ используем strip() при проверке ответа " "
                            response = data.decode('utf-8')
                            response_trimmed = response.strip()
                            
                            # Проверяем, не пришло ли сообщение о завершении сервера
                            if response_trimmed == "SERVER_SHUTDOWN":
                                shutdown_event.set()
                                print(f"\nСервер отключен")
                                os._exit(0)
                                return 0
                            elif response == " ":
                                # Это специальный ответ от сервера на неверный запрос
                                print(f"Ошибка: неверный запрос (сервер не распознал команду)")
                                response_received = True
                            elif response_trimmed:
                                # Проверяем, что ответ отличается от нашего запроса
                                # и содержит ответ от сервера
                                if "pong" in response_trimmed.lower() or "сервер" in response_trimmed.lower():
                                    print(f"{response_trimmed}")
                                    response_received = True
                                elif not response_trimmed.startswith(f"{client_number}:"):
                                    # Любой другой ответ, который не начинается с нашего номера
                                    print(f"{response_trimmed}")
                                    response_received = True
                            
                            # Очищаем файл только если получили ответ
                            if response_received:
                                os.ftruncate(fd, 0)

                        os.lockf(fd, os.F_ULOCK, 0)
                        os.close(fd)
                   
                    except Exception as e:
                        # Если файл не найден, значит сервер завершил работу
                        if isinstance(e, FileNotFoundError):
                            shutdown_event.set()
                            print(f"\nСервер отключен")
                            os._exit(0)
                            return 0
                        
                        try:
                            if 'fd' in locals():
                                os.lockf(fd, os.F_ULOCK, 0)
                                os.close(fd)
                        except:
                            pass
                        continue
                    
                    if not response_received and not shutdown_event.is_set():
                        time.sleep(0.1)
                
                if shutdown_event.is_set():
                    print(f"\nСервер отключен")
                    os._exit(0)
                    return 0
                
                if not response_received:
                    print(f"Таймаут: сервер не ответил")
                
                print()
           
            except FileNotFoundError:
                shutdown_event.set()
                print(f"\nСервер отключен")
                os._exit(0)
                return 0
            except OSError as e:
                if e.errno == errno.EACCES:
                    print(f"Ошибка доступа к файлу")
                else:
                    shutdown_event.set()
                    print(f"\nСервер отключен")
                    os._exit(0)
                return 0
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
                break
    
    except KeyboardInterrupt:
        print(f"\nКлиент №{client_number} завершает работу...")
        shutdown_event.set()
        
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
        
        os._exit(0)
    
    # Даем время мониторинговому потоку завершиться
    shutdown_event.set()
    time.sleep(0.5)
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <server_id>")
        print("Пример: python client.py server1")
        sys.exit(1)
    
    server_id = sys.argv[1]
    sys.exit(client(server_id))
