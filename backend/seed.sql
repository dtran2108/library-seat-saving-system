-- seed.sql — Development seed data for the Library Seat Saving System.
--
-- Contains only INSERT OR IGNORE statements with explicit PKs.
-- Idempotent: safe to re-run on an existing database — rows that already
-- exist (matched on PK) are silently skipped.
--
-- Layout reference:
--   Learning Plaza A/B : 4 cols → 2 rows × 4 seats each  (8 seats/zone)
--   Computer Area      : 3 cols → 2 rows × 3 seats        (6 seats)
--   Quiet Study Room   : 4 cols → 1 row  × 4 seats        (4 seats)
--   Total              : 4 zones, 26 seats

-- ── Zones ─────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO zones (zoneId, name,               location,    cols, status) VALUES
    (1, 'Learning Plaza A', '1st Floor',  4, 'active'),
    (2, 'Learning Plaza B', '1st Floor',  4, 'active'),
    (3, 'Computer Area',    '4th Floor',  3, 'active'),
    (4, 'Quiet Study Room', '3rd Floor',  4, 'active');

-- ── Seats: Learning Plaza A — 8 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    ( 1, 1, 'A-01', 'available'),
    ( 2, 1, 'A-02', 'available'),
    ( 3, 1, 'A-03', 'available'),
    ( 4, 1, 'A-04', 'occupied'),
    ( 5, 1, 'A-05', 'available'),
    ( 6, 1, 'A-06', 'available'),
    ( 7, 1, 'A-07', 'blocked'),
    ( 8, 1, 'A-08', 'available');

-- ── Seats: Learning Plaza B — 8 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    ( 9, 2, 'B-01', 'available'),
    (10, 2, 'B-02', 'available'),
    (11, 2, 'B-03', 'occupied'),
    (12, 2, 'B-04', 'available'),
    (13, 2, 'B-05', 'available'),
    (14, 2, 'B-06', 'available'),
    (15, 2, 'B-07', 'available'),
    (16, 2, 'B-08', 'occupied');

-- ── Seats: Computer Area — 6 seats ────────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (17, 3, 'C-01', 'available'),
    (18, 3, 'C-02', 'available'),
    (19, 3, 'C-03', 'occupied'),
    (20, 3, 'C-04', 'available'),
    (21, 3, 'C-05', 'blocked'),
    (22, 3, 'C-06', 'available');

-- ── Seats: Quiet Study Room — 4 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (23, 4, 'Q-01', 'available'),
    (24, 4, 'Q-02', 'available'),
    (25, 4, 'Q-03', 'available'),
    (26, 4, 'Q-04', 'available');
