from cassandra.cluster import Cluster
import uuid

# Подключение к Cassandra
cluster = Cluster(['127.0.0.1', '172.21.0.4', '172.21.0.3'])
session = cluster.connect()

session.execute("""
    CREATE KEYSPACE IF NOT EXISTS ticket_system 
    WITH replication = {'class' : 'NetworkTopologyStrategy', 'replication_factor': 3}
""")
session.set_keyspace('ticket_system')

session.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id UUID PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT,
        created_at TIMESTAMP
    );
""")
session.execute("CREATE INDEX IF NOT EXISTS ON users (username);")


session.execute("""
    CREATE TABLE IF NOT EXISTS client_ticket (
        client_id UUID,
        created_at TIMESTAMP,
        ticket_id UUID,
        status TEXT,
        PRIMARY KEY ((client_id), created_at)
    ) WITH CLUSTERING ORDER BY (created_at DESC);
""")
session.execute("CREATE INDEX IF NOT EXISTS ON client_ticket (status);")


session.execute("""
    CREATE TABLE IF NOT EXISTS worker_ticket (
        worker_id UUID,
        created_at TIMESTAMP,
        ticket_id UUID,
        status TEXT,
        PRIMARY KEY ((worker_id), created_at)
    ) WITH CLUSTERING ORDER BY (created_at DESC);
""")
session.execute("CREATE INDEX IF NOT EXISTS ON worker_ticket (status);")


session.execute("""
    CREATE TABLE IF NOT EXISTS ticket_details (
        ticket_id UUID PRIMARY KEY,
        client_id UUID,
        worker_id UUID,
        description TEXT,
        status TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    );
""")
session.execute("CREATE INDEX IF NOT EXISTS ON ticket_details (status);")

session.execute("""
    CREATE TABLE IF NOT EXISTS archived_tickets (
        ticket_id UUID PRIMARY KEY,
        client_id UUID,
        worker_id UUID,
        description TEXT,
        status TEXT,
        created_at TIMESTAMP,
        closed_at TIMESTAMP
    );
""")
session.execute("CREATE INDEX IF NOT EXISTS ON ticket_details (worker_id);")
session.execute("CREATE INDEX IF NOT EXISTS ON archived_tickets (closed_at);")

print("Схема базы данных успешно создана!")

cluster.shutdown()
