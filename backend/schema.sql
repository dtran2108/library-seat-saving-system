-- schema.sql — DDL for the Library Seat Saving System.
--
-- Contains only structure: CREATE TABLE and CREATE TRIGGER statements.
-- Seed data lives in seed.sql.
-- Both files are executed by init_db() in db.py on every server start.
-- IF NOT EXISTS / DROP-free DDL makes this safe to re-run on an existing DB.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────
-- User
-- Attributes: uId (PK), uname, phoneNo, password, role, ustatus
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    uId      TEXT PRIMARY KEY,                          -- Student ID (e.g. "B123456789")
    uname    TEXT NOT NULL,
    phoneNo  TEXT,
    password TEXT NOT NULL,                             -- Werkzeug-hashed
    role     TEXT NOT NULL DEFAULT 'user'
                 CHECK (role IN ('user', 'admin')),
    ustatus  TEXT NOT NULL DEFAULT 'active'
                 CHECK (ustatus IN ('active', 'suspended'))
);

-- ─────────────────────────────────────────────────────────────
-- Zone  (normalized from Seat.location / Seat.zone)
-- Represents a named physical area inside the library.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS zones (
    zoneId   INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,                          -- e.g. 'Learning Plaza A'
    location TEXT    NOT NULL,                          -- e.g. '2nd Floor, North Wing'
    cols     INTEGER NOT NULL DEFAULT 4,                -- seats per row in the physical grid
    status   TEXT    NOT NULL DEFAULT 'active'
                 CHECK (status IN ('active', 'maintenance'))
);

-- ─────────────────────────────────────────────────────────────
-- Seat
-- Attributes: seatId (PK), zoneId (FK→zones), destNo, status
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS seats (
    seatId INTEGER PRIMARY KEY AUTOINCREMENT,
    zoneId INTEGER NOT NULL,
    destNo TEXT    NOT NULL,                            -- Desk label within zone, e.g. 'A-01'
    status TEXT    NOT NULL DEFAULT 'available'
               CHECK (status IN ('available', 'booked', 'maintenance')),
    FOREIGN KEY (zoneId) REFERENCES zones(zoneId)
);

-- ─────────────────────────────────────────────────────────────
-- Reservation
-- Relationships: User -Makes-> Reservation (1:N)
--                Seat -Reserves-> Reservation (1:N)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    reservationId INTEGER PRIMARY KEY AUTOINCREMENT,
    uId           TEXT     NOT NULL,
    seatId        INTEGER  NOT NULL,
    startTime     DATETIME NOT NULL,
    endTime       DATETIME NOT NULL,
    status        TEXT     NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'cancelled', 'completed', 'no_show')),
    createdAt     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uId)    REFERENCES users(uId),
    FOREIGN KEY (seatId) REFERENCES seats(seatId)
);

-- ─────────────────────────────────────────────────────────────
-- CheckInLog  (weak entity — double rectangle in ER diagram)
-- Relationship: Reservation -TrackedBy-> CheckInLog (1:1)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS check_in_logs (
    checkInId     INTEGER PRIMARY KEY AUTOINCREMENT,
    reservationId INTEGER NOT NULL UNIQUE,
    checkInTime   DATETIME,
    checkOutTime  DATETIME,
    status        TEXT NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending', 'checked_in', 'checked_out', 'no_show')),
    FOREIGN KEY (reservationId) REFERENCES reservations(reservationId)
);

-- ─────────────────────────────────────────────────────────────
-- Penalty
-- Relationship: User -Receives-> Penalty (1:N)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS penalties (
    penaltyId INTEGER PRIMARY KEY AUTOINCREMENT,
    uId       TEXT NOT NULL,
    reason    TEXT NOT NULL,
    startDate DATE NOT NULL,
    endDate   DATE NOT NULL,
    status    TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'expired')),
    FOREIGN KEY (uId) REFERENCES users(uId)
);

-- ─────────────────────────────────────────────────────────────
-- AdminActionLog
-- Relationships: User(admin) -Performs-> AdminActionLog (1:N)
--                Penalty -ResultsIn-> AdminActionLog (1:1, optional)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin_action_logs (
    actionId   INTEGER PRIMARY KEY AUTOINCREMENT,
    uId        TEXT     NOT NULL,
    actionType TEXT     NOT NULL,
    timeStamp  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    targetId   TEXT     NOT NULL,
    penaltyId  INTEGER,
    FOREIGN KEY (uId)       REFERENCES users(uId),
    FOREIGN KEY (penaltyId) REFERENCES penalties(penaltyId)
);

-- ─────────────────────────────────────────────────────────────
-- Trigger: auto-release seat on no-show
-- Fires when a check_in_log row is updated to status = 'no_show'.
-- Marks the linked reservation no_show and frees the seat.
-- ─────────────────────────────────────────────────────────────
CREATE TRIGGER IF NOT EXISTS auto_release_seat
AFTER UPDATE OF status ON check_in_logs
WHEN NEW.status = 'no_show'
BEGIN
    UPDATE reservations
    SET    status = 'no_show'
    WHERE  reservationId = NEW.reservationId;

    UPDATE seats
    SET    status = 'available'
    WHERE  seatId = (SELECT seatId FROM reservations WHERE reservationId = NEW.reservationId);
END;
