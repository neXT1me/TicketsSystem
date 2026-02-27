from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider  # Если требуется аутентификация

# Подключение к кластеру (для локального сервера)
cluster = Cluster(['localhost'], port=9042)

session = cluster.connect()

# Проверка подключения: список ключевых пространств
try:
    rows = session.execute("SELECT keyspace_name FROM system_schema.keyspaces;")
    print("Подключение успешно! Доступные keyspaces:")
    for row in rows:
        print(row.keyspace_name)
except Exception as e:
    print(f"Ошибка подключения: {e}")
finally:
    cluster.shutdown()