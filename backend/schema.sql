-- schema.sql — Database schema for the Library Seat Saving System.
--
-- Tables are derived from the ER model (ER-models.png) with one
-- normalization: Seat's flat location/zone TEXT columns are extracted
-- into a proper `zones` table.  Each zone represents a named physical
-- area (e.g. a learning plaza); seats belong to exactly one zone.
--
-- Run via init_db() in db.py (uses IF NOT EXISTS — safe to re-run).
-- Seed data uses INSERT OR IGNORE with explicit PKs — idempotent.

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
-- Removed: location TEXT, zone TEXT  (now in zones table)
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
-- (Implements the "Auto-Release Seats" system requirement.)
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

-- ─────────────────────────────────────────────────────────────
-- Seed Data — zones and seats
--
-- INSERT OR IGNORE with explicit PKs makes this block idempotent:
-- on the first run it inserts; on subsequent startups it is a no-op.
-- ─────────────────────────────────────────────────────────────
-- cols = seats per row in the physical grid layout
--   Plaza A/B: 4 cols → 2 rows × 4 seats
--   Computer:  3 cols → 2 rows × 3 seats
--   Quiet:     4 cols → 1 row  × 4 seats
INSERT OR IGNORE INTO zones (zoneId, name, location, cols, status) VALUES
    (1, 'Learning Plaza A', '1st Floor', 4, 'active'),
    (2, 'Learning Plaza B', '1st Floor', 4, 'active'),
    (3, 'Computer Area',    '4th Floor',             3, 'active'),

-- Learning Plaza A — 8 seats
INSERT OR IGNORE INTO seats (seatId, zoneId, destNo, status) VALUES
    ( 1, 1, 'A-01', 'available'),
    ( 2, 1, 'A-02', 'available'),
    ( 3, 1, 'A-03', 'available'),
    ( 4, 1, 'A-04', 'booked'),
    ( 5, 1, 'A-05', 'available'),
    ( 6, 1, 'A-06', 'available'),
    ( 7, 1, 'A-07', 'maintenance'),
    ( 8, 1, 'A-08', 'available');

-- Learning Plaza B — 8 seats
INSERT OR IGNORE INTO seats (seatId, zoneId, destNo, status) VALUES
    ( 9, 2, 'B-01', 'available'),
    (10, 2, 'B-02', 'available'),
    (11, 2, 'B-03', 'booked'),
    (12, 2, 'B-04', 'available'),
    (13, 2, 'B-05', 'available'),
    (14, 2, 'B-06', 'available'),
    (15, 2, 'B-07', 'available'),
    (16, 2, 'B-08', 'booked');

-- Computer Area — 6 seats
INSERT OR IGNORE INTO seats (seatId, zoneId, destNo, status) VALUES
    (17, 3, 'C-01', 'available'),
    (18, 3, 'C-02', 'available'),
    (19, 3, 'C-03', 'booked'),
    (20, 3, 'C-04', 'available'),
    (21, 3, 'C-05', 'maintenance'),
    (22, 3, 'C-06', 'available');
