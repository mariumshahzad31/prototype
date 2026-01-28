import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DB_PATH = Path(__file__).parent / "aura.db"


class Database:
    """
    Thread-safe SQLite helper for AURA.

    Schema (high level):
      - users(id, username, created_at)
      - devices(id, user_id, name, node_label, last_seen_at, status)
      - profiles(id, user_id, profile_path, created_at, learning_complete)
      - events(id, user_id, device_id, timestamp, source_ip, dest_ip, protocol,
               bytes_sent, bytes_recv, is_anomaly, anomaly_score, raw_features_json)
      - alerts(id, user_id, device_id, event_id, created_at, severity,
               title, message, explained_message, resolved)
      - firewall_actions(id, user_id, device_id, event_id, created_at,
                         action, rule_ref)
    """

    def __init__(self, path: Path = DB_PATH) -> None:
        self.path = Path(path)
        # `check_same_thread=False` so that connections can be shared across threads;
        # we still serialize access via a lock.
        self._lock = threading.RLock()
        self._ensure_schema()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._lock, self._conn() as conn:
            c = conn.cursor()

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    node_label TEXT NOT NULL, -- e.g. 'S1', 'S2'
                    last_seen_at TEXT,
                    status TEXT DEFAULT 'offline',
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    profile_path TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    learning_complete INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                );
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    device_id INTEGER,
                    timestamp TEXT NOT NULL,
                    source_ip TEXT,
                    dest_ip TEXT,
                    protocol TEXT,
                    bytes_sent INTEGER,
                    bytes_recv INTEGER,
                    is_anomaly INTEGER,
                    anomaly_score REAL,
                    raw_features_json TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                );
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    device_id INTEGER,
                    event_id INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    explained_message TEXT,
                    resolved INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id),
                    FOREIGN KEY(event_id) REFERENCES events(id)
                );
                """
            )

            c.execute(
                """
                CREATE TABLE IF NOT EXISTS firewall_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    device_id INTEGER,
                    event_id INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    action TEXT NOT NULL, -- e.g. 'block_ip', 'allow', 'log_only'
                    rule_ref TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id),
                    FOREIGN KEY(event_id) REFERENCES events(id)
                );
                """
            )

    # Generic helpers
    def execute(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> int:
        with self._lock, self._conn() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.lastrowid

    def fetchall(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> List[sqlite3.Row]:
        with self._lock, self._conn() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return list(c.fetchall())

    def fetchone(
        self, query: str, params: Tuple[Any, ...] = ()
    ) -> Optional[sqlite3.Row]:
        with self._lock, self._conn() as conn:
            c = conn.cursor()
            c.execute(query, params)
            row = c.fetchone()
            return row

    # Domain-specific helpers
    def get_or_create_user(self, username: str) -> int:
        row = self.fetchone(
            "SELECT id FROM users WHERE username = ?", (username,)
        )
        if row:
            return int(row["id"])
        return self.execute(
            "INSERT INTO users(username) VALUES (?)", (username,)
        )

    def upsert_device(
        self, user_id: int, name: str, node_label: str, status: str = "online"
    ) -> int:
        existing = self.fetchone(
            """
            SELECT id FROM devices
            WHERE user_id = ? AND node_label = ?
            """,
            (user_id, node_label),
        )
        if existing:
            device_id = int(existing["id"])
            self.execute(
                """
                UPDATE devices
                SET name = ?, status = ?, last_seen_at = datetime('now')
                WHERE id = ?
                """,
                (name, status, device_id),
            )
            return device_id
        return self.execute(
            """
            INSERT INTO devices(user_id, name, node_label, status, last_seen_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (user_id, name, node_label, status),
        )

    def insert_profile(
        self, user_id: int, profile_path: str, learning_complete: bool
    ) -> int:
        return self.execute(
            """
            INSERT INTO profiles(user_id, profile_path, learning_complete)
            VALUES (?, ?, ?)
            """,
            (user_id, profile_path, int(learning_complete)),
        )

    def insert_event(
        self,
        user_id: int,
        device_id: Optional[int],
        timestamp: str,
        source_ip: str,
        dest_ip: str,
        protocol: str,
        bytes_sent: int,
        bytes_recv: int,
        is_anomaly: bool,
        anomaly_score: float,
        raw_features_json: str,
    ) -> int:
        return self.execute(
            """
            INSERT INTO events(
                user_id, device_id, timestamp, source_ip, dest_ip,
                protocol, bytes_sent, bytes_recv, is_anomaly,
                anomaly_score, raw_features_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                device_id,
                timestamp,
                source_ip,
                dest_ip,
                protocol,
                bytes_sent,
                bytes_recv,
                int(is_anomaly),
                anomaly_score,
                raw_features_json,
            ),
        )

    def insert_alert(
        self,
        user_id: int,
        device_id: Optional[int],
        event_id: int,
        severity: str,
        title: str,
        message: str,
        explained_message: Optional[str] = None,
    ) -> int:
        return self.execute(
            """
            INSERT INTO alerts(
                user_id, device_id, event_id, severity,
                title, message, explained_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                device_id,
                event_id,
                severity,
                title,
                message,
                explained_message,
            ),
        )

    def insert_firewall_action(
        self,
        user_id: int,
        device_id: Optional[int],
        event_id: int,
        action: str,
        rule_ref: Optional[str],
    ) -> int:
        return self.execute(
            """
            INSERT INTO firewall_actions(
                user_id, device_id, event_id, action, rule_ref
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, device_id, event_id, action, rule_ref),
        )

    def recent_events(self, limit: int = 500) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            """
            SELECT * FROM events
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in rows]

    def recent_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            """
            SELECT * FROM alerts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(r) for r in rows]

    # Convenience methods for the demo UI
    def get_all_devices(self) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            """
            SELECT id, user_id, name, node_label, last_seen_at, status FROM devices
            ORDER BY id ASC
            """
        )
        return [dict(r) for r in rows]

    def _bootstrap_demo_data_if_empty(self) -> None:
        """Populate the DB with lightweight demo user, devices and events if empty.

        This is intended for local demos and testing only.
        """
        # Check if we have any events; if so, assume DB is populated
        row = self.fetchone("SELECT COUNT(*) as cnt FROM events")
        if row and int(row["cnt"]) > 0:
            return

        # Create a demo user
        demo_username = "demo"
        user_id = self.get_or_create_user(demo_username)

        # Create two devices S1 and S2
        s1 = self.upsert_device(user_id, "Local Gateway", "S1", status="online")
        s2 = self.upsert_device(user_id, "Remote Edge", "S2", status="online")

        now = datetime.utcnow()

        # Insert synthetic events for the last 48 hours
        for i in range(120):
            ts = (now - timedelta(minutes=10 * i)).isoformat()
            src = "192.168.1.%d" % (2 + (i % 10)) if i % 3 != 0 else f"198.51.100.{10 + (i%20)}"
            dst = "10.0.0.5"
            proto = "TCP" if i % 4 != 0 else "UDP"
            sent = random.randint(40, 1200)
            recv = random.randint(0, 800)
            is_anom = 1 if (i % 37 == 0) else 0
            score = random.random() * 0.9 + (0.1 if is_anom else 0)
            raw = json.dumps({"sample": True, "i": i})
            device_id = s1 if (i % 2 == 0) else s2
            try:
                self.insert_event(
                    user_id=user_id,
                    device_id=device_id,
                    timestamp=ts,
                    source_ip=src,
                    dest_ip=dst,
                    protocol=proto,
                    bytes_sent=sent,
                    bytes_recv=recv,
                    is_anomaly=bool(is_anom),
                    anomaly_score=float(score),
                    raw_features_json=raw,
                )
            except Exception:
                # best-effort demo data population
                continue

        # Optionally insert a demo alert
        try:
            recent = self.fetchone("SELECT id FROM events ORDER BY timestamp DESC LIMIT 1")
            if recent:
                self.insert_alert(
                    user_id=user_id,
                    device_id=s2,
                    event_id=int(recent["id"]),
                    severity="HIGH",
                    title="Demo: Suspicious traffic",
                    message="Multiple connections from unusual IPs",
                    explained_message="Synthetic demo alert generated for UI purposes",
                )
        except Exception:
            pass

