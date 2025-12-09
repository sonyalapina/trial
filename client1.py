import os
import sys
import time
import errno

shared_file = "shared_memory.txt"
clients_file = "clients_count.txt"


def client(server_id):
    # Регистрируем клиента
    try:
        fd = os.open(clients_file, os.O_RDWR)
        os.lockf(fd, os.F_LOCK, 0)

        data = os.read(fd, 1024)
        current_clients = int(data.decode("utf-8") or "0")
        client_number = current_clients + 1

        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, str(client_number).encode("utf-8"))
        os.ftruncate(fd, len(str(client_number)))

        os.lockf(fd, os.F_ULOCK, 0)
        os.close(fd)

    except Exception as e:
        print("Ошибка при регистрации клиента:", e)
        return 1

    print(f"Клиент №{client_number} подключён к серверу [{server_id}]\n")

    try:
        while True:
            user_input = input(f"Клиент №{client_number} → Введите сообщение: ")

            try:
                # Пишем запрос
                fd = os.open(shared_file, os.O_RDWR)
                os.lockf(fd, os.F_LOCK, 0)

                request_data = f"{client_number}:{user_input}"
                os.lseek(fd, 0, os.SEEK_SET)
                os.write(fd, request_data.encode("utf-8"))
                os.fsync(fd)

                os.lockf(fd, os.F_ULOCK, 0)
                os.close(fd)

                response_received = False
                timeout = 5
                start_time = time.time()

                while not response_received and (time.time() - start_time) < timeout:
                    try:
                        fd = os.open(shared_file, os.O_RDWR)
                        os.lockf(fd, os.F_LOCK, 0)

                        os.lseek(fd, 0, os.SEEK_SET)
                        data = os.read(fd, 1024)

                        if data:
                            response = data.decode("utf-8").strip()

                            # --- Ловим отключение сервера ---
                            if response == "__SERVER_DOWN__":
                                print(f"Клиент №{client_number}: сервер отключился")
                                os.ftruncate(fd, 0)
                                os.lockf(fd, os.F_ULOCK, 0)
                                os.close(fd)
                                return 0
                            # --- конец добавки ---

                            if response == " ":
                                print(f"Клиент №{client_number}: Ошибка: неверный запрос")
                                response_received = True
                            else:
                                # Ответ должен быть от сервера (не наш запрос)
                                if not response.startswith(f"{client_number}:"):
                                    print(f"Клиент №{client_number}: {response}")
                                    response_received = True

                            if response_received:
                                os.ftruncate(fd, 0)

                        os.lockf(fd, os.F_ULOCK, 0)
                        os.close(fd)

                    except Exception:
                        try:
                            if "fd" in locals():
                                os.lockf(fd, os.F_ULOCK, 0)
                                os.close(fd)
                        except:
                            pass

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

        # Уменьшаем счётчик клиентов
        try:
            fd = os.open(clients_file, os.O_RDWR)
            os.lockf(fd, os.F_LOCK, 0)

            data = os.read(fd, 1024).decode("utf-8") or "0"
            current_clients = int(data)

            new_count = max(0, current_clients - 1)
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, str(new_count).encode("utf-8"))
            os.ftruncate(fd, len(str(new_count)))

            os.lockf(fd, os.F_ULOCK, 0)
            os.close(fd)
        except:
            pass

    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python client.py <server_id>")
        sys.exit(1)

    server_id = sys.argv[1]
    sys.exit(client(server_id))
