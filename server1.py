import os
import sys
import time
import errno

shared_file = "shared_memory.txt"
clients_file = "clients_count.txt"


def server(server_id):
    print(f"Сервер [{server_id}] запущен")
    print("Сервер ждёт сообщений от клиентов...\n")

    # Создаём shared_file, если его нет
    if not os.path.exists(shared_file):
        with open(shared_file, "w") as f:
            f.write("")

    # Создаём clients_file, если его нет
    if not os.path.exists(clients_file):
        with open(clients_file, "w") as f:
            f.write("0")

    try:
        while True:
            try:
                fd = os.open(shared_file, os.O_RDWR)

                # Блокировка файла
                os.lockf(fd, os.F_LOCK, 0)

                os.lseek(fd, 0, os.SEEK_SET)
                data = os.read(fd, 1024)

                if data:
                    request = data.decode("utf-8").strip()

                    if request:
                        # Формат: X:message
                        if ":" not in request:
                            response = " "
                        else:
                            client_num, message = request.split(":", 1)
                            response = f"Ответ от сервера [{server_id}]: {message[::-1]}"

                        # Пишем ответ
                        os.lseek(fd, 0, os.SEEK_SET)
                        os.write(fd, response.encode("utf-8"))
                        os.ftruncate(fd, len(response))

                os.lockf(fd, os.F_ULOCK, 0)
                os.close(fd)

                time.sleep(0.1)

            except Exception:
                try:
                    if "fd" in locals():
                        os.lockf(fd, os.F_ULOCK, 0)
                        os.close(fd)
                except:
                    pass
                continue

    except KeyboardInterrupt:
        print("\nСервер завершает работу...")

        # Посылаем клиентам сигнал отключения
        try:
            fd = os.open(shared_file, os.O_RDWR)
            os.lockf(fd, os.F_LOCK, 0)

            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, b"__SERVER_DOWN__")
            os.ftruncate(fd, len("__SERVER_DOWN__"))

            os.lockf(fd, os.F_ULOCK, 0)
            os.close(fd)
        except:
            pass

        print("Сервер корректно завершён.")
        return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python server.py <server_id>")
        sys.exit(1)

    server_id = sys.argv[1]
    sys.exit(server(server_id))
