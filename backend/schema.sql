-- schema.sql — DDL for the Library Seat Saving System.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────
-- Clean slate — drop in reverse FK order so dependents go first.
-- ─────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS auto_release_seat;
DROP TABLE   IF EXISTS admin_action_logs;
DROP TABLE   IF EXISTS penalties;
DROP TABLE   IF EXISTS check_in_logs;
DROP TABLE   IF EXISTS reservations;
DROP TABLE   IF EXISTS seats;
DROP TABLE   IF EXISTS zones;
DROP TABLE   IF EXISTS users;

-- ─────────────────────────────────────────────────────────────
-- User
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    uId      TEXT PRIMARY KEY,
    uname    TEXT NOT NULL,
    phoneNo  TEXT,
    password TEXT NOT NULL,
    role     TEXT NOT NULL DEFAULT 'user'
                 CHECK (role IN ('user', 'admin')),
    ustatus  TEXT NOT NULL DEFAULT 'active'
                 CHECK (ustatus IN ('active', 'suspended'))
);

-- ─────────────────────────────────────────────────────────────
-- Zone
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS zones (
    zoneId   INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,
    location TEXT    NOT NULL,
    cols     INTEGER NOT NULL DEFAULT 4,
    status   TEXT    NOT NULL DEFAULT 'active'
                 CHECK (status IN ('active', 'maintenance'))
);

-- ─────────────────────────────────────────────────────────────
-- Seat
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS seats (
    seatId INTEGER PRIMARY KEY AUTOINCREMENT,
    zoneId INTEGER NOT NULL,
    deskNo TEXT    NOT NULL,
    status TEXT    NOT NULL DEFAULT 'available'
               CHECK (status IN ('available', 'occupied', 'blocked')),
    FOREIGN KEY (zoneId) REFERENCES zones(zoneId)
);

-- ─────────────────────────────────────────────────────────────
-- Reservation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reservations (
    reservationId INTEGER  PRIMARY KEY AUTOINCREMENT,
    userId        TEXT     NOT NULL,
    seatId        INTEGER  NOT NULL,
    startTime     DATETIME NOT NULL,
    endTime       DATETIME NOT NULL,
    status        TEXT     NOT NULL DEFAULT 'upcoming'
                      CHECK (status IN ('upcoming', 'active', 'completed', 'cancelled', 'no_show')),
    createdAt     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES users(uId),
    FOREIGN KEY (seatId) REFERENCES seats(seatId)
);

-- ─────────────────────────────────────────────────────────────
-- CheckInLog
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS check_in_logs (
    checkInId     INTEGER  PRIMARY KEY AUTOINCREMENT,
    reservationId INTEGER  NOT NULL UNIQUE,
    checkInTime   DATETIME,
    checkOutTime  DATETIME,
    status        TEXT     NOT NULL DEFAULT 'checked_in'
                      CHECK (status IN ('checked_in', 'checked_out', 'missed')),
    FOREIGN KEY (reservationId) REFERENCES reservations(reservationId)
);

-- ─────────────────────────────────────────────────────────────
-- Penalty
-- reservationId is nullable: an admin may issue a manual penalty not tied
-- to a specific reservation.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS penalties (
    penaltyId     INTEGER PRIMARY KEY AUTOINCREMENT,
    reservationId INTEGER,
    reason        TEXT    NOT NULL,
    startDate     DATE    NOT NULL,
    endDate       DATE    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'expired', 'revoked')),
    FOREIGN KEY (reservationId) REFERENCES reservations(reservationId)
);

-- ─────────────────────────────────────────────────────────────
-- AdminActionLog
-- seatId and penaltyId are both nullable because each actionType targets
-- a different entity (block_seat → seatId; issue_penalty → penaltyId; etc.).
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admin_action_logs (
    actionId   INTEGER  PRIMARY KEY AUTOINCREMENT,
    userId     TEXT     NOT NULL,
    seatId     INTEGER,
    penaltyId  INTEGER,
    actionType TEXT     NOT NULL
                   CHECK (actionType IN (
                       'block_seat', 'unblock_seat', 'cancel_reservation',
                       'issue_penalty', 'revoke_penalty',
                       'suspend_user', 'reactivate_user'
                   )),
    timeStamp  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId)    REFERENCES users(uId),
    FOREIGN KEY (seatId)    REFERENCES seats(seatId),
    FOREIGN KEY (penaltyId) REFERENCES penalties(penaltyId)
);

-- ─────────────────────────────────────────────────────────────
-- Trigger: auto-release seat on missed check-in
-- ─────────────────────────────────────────────────────────────
CREATE TRIGGER IF NOT EXISTS auto_release_seat
AFTER UPDATE OF status ON check_in_logs
WHEN NEW.status = 'missed'
BEGIN
    UPDATE reservations
    SET    status = 'no_show'
    WHERE  reservationId = NEW.reservationId;

    UPDATE seats
    SET    status = 'available'
    WHERE  seatId = (SELECT seatId FROM reservations WHERE reservationId = NEW.reservationId);
END;
