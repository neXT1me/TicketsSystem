from cassandra.cluster import Cluster
import uuid

# Подключение к Cassandra
cluster = Cluster(['127.0.0.1'])  # Укажите адрес вашей Cassandra
session = cluster.connect('ticket_system')


def register() -> None:
    # --- ФУНКЦИЯ РЕГИСТРАЦИИ ---
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    role = input("Введите вашу роль (client/worker): ")

    user_id = uuid.uuid4()

    session.execute("INSERT INTO users (user_id, username, password, role) VALUES (%s, %s, %s, %s)",
                    [user_id, username, password, role])
    print(f"Пользователь {username} успешно создан!")


def authenticate() -> tuple[None, None]:
    # --- ФУНКЦИЯ АВТОРИЗАЦИИ ---
    username = input("Введите имя пользователя: ")

    user = session.execute("SELECT user_id, role FROM users WHERE username = %s", [username]).one()

    if user:
        print(f"Успешный вход! Роль: {user.role}")
        return user.user_id, user.role
    else:
        print("Ошибка: Неверный логин или пароль.")
        return None, None


def view_my_tickets(user_id: str, role: str) -> None:
    # --- ПРОСМОТР СВОИХ ЗАЯВОК (клиент/рабочий) ---
    if role == "client":
        rows = session.execute("SELECT ticket_id, status FROM client_ticket WHERE client_id = %s", [user_id])
    elif role == "worker":
        rows = session.execute("SELECT ticket_id, status FROM worker_ticket WHERE worker_id = %s", [user_id])
    else:
        print("Ошибка: Некорректная роль")
        return

    for row in rows:
        print(f"Заявка {row.ticket_id} - Статус: {row.status}")


def view_all_tickets(role: str):
    # --- ПРОСМОТР ВСЕХ ЗАЯВОК (ТОЛЬКО ДЛЯ РАБОЧИХ) ---
    if role == 'worker':
        rows = session.execute("SELECT client_id, ticket_id, worker_id FROM all_ticket WHERE status = 'open'")

        for i, (row) in enumerate(rows):
            print(f"Заявка {row.ticket_id} (Клиент: {row.client_id}, Рабочий: {row.worker_id})")

    else:
        print('Отказано в Доступе')


def view_ticket_details(ticket_id: str) -> None:
    # --- ПРОСМОТР СВЕДЕНИЙ О ЗАЯВКЕ ---
    ticket_id = uuid.UUID(input("Введите ID заявки: "))
    row = session.execute("SELECT client_id, worker_id, status, description FROM ticket_details WHERE ticket_id = %s",
                          [ticket_id]).one()
    if row:
        print(
            f"Заявка {ticket_id}\n Клиент: {row.client_id}\n Рабочий: {row.worker_id}\n Статус: {row.status}\n Описание: {row.description}")
    else:
        print("Заявка не найдена")


def create_ticket(client_id: str) -> None:
    # --- СОЗДАНИЕ ЗАЯВКИ (Клиент) ---
    ticket_id = uuid.uuid4()
    description = input("Введите описание заявки: ")

    session.execute("INSERT INTO client_ticket (client_id, ticket_id, status) VALUES (%s, %s, %s)",
                    [client_id, ticket_id, "open"])
    session.execute("INSERT INTO all_ticket (client_id, ticket_id, worker_id, status) VALUES (%s, %s, %s, %s)",
                    [client_id, ticket_id, None, "open"])
    session.execute(
        "INSERT INTO ticket_details (ticket_id, client_id, worker_id, status, description) VALUES (%s, %s, %s, %s, %s)",
        [ticket_id, client_id, None, "open", description])

    print(f"Заявка {ticket_id} создана!")


def update_ticket_status(worker_id: str) -> None:
    # --- ИЗМЕНЕНИЕ СТАТУСА ЗАЯВКИ (Рабочий) ---
    try:
        ticket_id = uuid.UUID(input("Введите ID заявки: "))
        new_status = input("Введите новый статус (open/closed/in_progress): ")

        # Получаем текущие данные заявки
        row = session.execute("SELECT client_id, worker_id, description FROM ticket_details WHERE ticket_id = %s",
                              [ticket_id]).one()
        if not row:
            print("Заявка не найдена")
            return

        client_id, description = row.client_id, row.description

        # Удаляем старую запись
        session.execute("DELETE FROM ticket_details WHERE ticket_id = %s", [ticket_id])
        session.execute("DELETE FROM worker_ticket WHERE worker_id = %s AND status = %s AND ticket_id = %s",
                        [worker_id, row.status, ticket_id])

        # Вставляем новую запись с обновленным статусом
        session.execute(
            "INSERT INTO ticket_details (ticket_id, client_id, worker_id, status, description) VALUES (%s, %s, %s, %s, %s)",
            [ticket_id, client_id, worker_id, new_status, description])
        session.execute("INSERT INTO all_ticket (status, ticket_id, client_id, worker_id) VALUES (%s, %s, %s, %s)",
                        [new_status, ticket_id, client_id, worker_id])
        session.execute("INSERT INTO worker_ticket (worker_id, status, ticket_id) VALUES (%s, %s, %s)",
                        [worker_id, new_status, ticket_id])

        print(f"Статус заявки {ticket_id} изменен на {new_status}")
    except ValueError:
        print("Ошибка: Неверный формат UUID")


def archive_ticket() -> None:
    # --- ПЕРЕНОС В АРХИВ ---
    ticket_id = input("Введите ID заявки для архивации: ")

    row = session.execute("SELECT client_id, worker_id, status, description FROM ticket_details WHERE ticket_id = %s",
                          [ticket_id]).one()

    if row:
        session.execute(
            "INSERT INTO archived_ticket (partition_key, ticket_id, client_id, worker_id, status, description) VALUES (%s, %s, %s, %s, %s, %s)",
            [hash(ticket_id) % 10, ticket_id, row.client_id, row.worker_id, row.status, row.description])
        session.execute("DELETE FROM ticket_details WHERE ticket_id = %s", [ticket_id])
        session.execute("DELETE FROM all_ticket WHERE ticket_id = %s", [ticket_id])

        print(f"Заявка {ticket_id} перенесена в архив.")
    else:
        print("Заявка не найдена")


def main() -> None:
    # --- КОНСОЛЬНОЕ МЕНЮ ---
    print("\n=== Система заявок (Cassandra) ===")
    index = input('Войти - 1 / Зарегистрироваться - 2: ')
    if index == '2':
        register()
        main()
    elif index == '1':
        user_id, role = authenticate()
        if not user_id:
            return

        while True:
            print("\nВыберите действие:")

            if role == "client":
                print("1: Просмотр своих заявок")
                print("2: Создать новую заявку")
            elif role == "worker":
                print("1: Просмотр своих заявок")
                print("2: Просмотр всех заявок")
                print("3: Изменение статуса заявки")
            print("4: Просмотр сведений о заявке")
            print("5: Архивировать заявку")
            print("9: Сменить пользователя")
            print("0: Выход из системы")

            choice = input("Введите номер действия: ")

            if choice == "1":
                view_my_tickets(user_id, role)
            elif choice == "2" and role == "client":
                create_ticket(user_id)
            elif choice == "2" and role == "worker":
                view_all_tickets(role)
            elif choice == "3" and role == "worker":
                update_ticket_status(user_id)
            elif choice == "4":
                ticket_id = input("Введите ID заявки: ")
                view_ticket_details(ticket_id)
            elif choice == "5":
                archive_ticket()
            elif choice == "9":
                main()
                break
            elif choice == "0":
                print("Выход из системы...")
                break
            else:
                print("Некорректный ввод")


if __name__ == "__main__":
    main()