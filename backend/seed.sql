-- seed.sql — Development seed data for the Library Seat Saving System.
--
-- Contains only INSERT OR IGNORE statements with explicit PKs.
-- Idempotent: safe to re-run on an existing database — rows that already
-- exist (matched on PK) are silently skipped.
--
-- Layout reference:
--   Learning Plaza A   : 7 cols → 7 rows × 7 seats each  (49 seats/zone)
--   Learning Plaza B   : 4 cols → 2 rows × 4 seats each  (8 seats/zone)
--   Computer Area      : 3 cols → 2 rows × 3 seats        (6 seats)
--   Quiet Study Room   : 4 cols → 1 row  × 4 seats        (4 seats)
--   Total              : 4 zones, 67 seats

-- ── Zones ─────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO zones (zoneId, name,               location,    cols, status) VALUES
    (1, 'Learning Plaza A', '1st Floor',  7, 'active'),
    (2, 'Learning Plaza B', '1st Floor',  4, 'active'),
    (3, 'Computer Area',    '4th Floor',  3, 'active'),
    (4, 'Quiet Study Room', '3rd Floor',  4, 'active');

-- ── Seats: Learning Plaza A — 49 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    ( 1, 1, 'A-01', 'available'),
    ( 2, 1, 'A-02', 'available'),
    ( 3, 1, 'A-03', 'available'),
    ( 4, 1, 'A-04', 'occupied'),
    ( 5, 1, 'A-05', 'available'),
    ( 6, 1, 'A-06', 'available'),
    ( 7, 1, 'A-07', 'blocked'),
    ( 8, 1, 'A-08', 'available'),
    ( 9, 1, 'A-09', 'available'),
    (10, 1, 'A-10', 'available'),
    (11, 1, 'A-11', 'available'),
    (12, 1, 'A-12', 'available'),
    (13, 1, 'A-13', 'available'),
    (14, 1, 'A-14', 'available'),
    (15, 1, 'A-15', 'available'),
    (16, 1, 'A-16', 'available'),
    (17, 1, 'A-17', 'available'),
    (18, 1, 'A-18', 'available'),
    (19, 1, 'A-19', 'available'),
    (20, 1, 'A-20', 'available'),
    (21, 1, 'A-21', 'available'),
    (22, 1, 'A-22', 'available'),
    (23, 1, 'A-23', 'available'),
    (24, 1, 'A-24', 'available'),
    (25, 1, 'A-25', 'available'),
    (26, 1, 'A-26', 'available'),
    (27, 1, 'A-27', 'available'),
    (28, 1, 'A-28', 'available'),
    (29, 1, 'A-29', 'available'),
    (30, 1, 'A-30', 'available'),
    (31, 1, 'A-31', 'available'),
    (32, 1, 'A-32', 'available'),
    (33, 1, 'A-33', 'available'),
    (34, 1, 'A-34', 'available'),
    (35, 1, 'A-35', 'available'),
    (36, 1, 'A-36', 'available'),
    (37, 1, 'A-37', 'available'),
    (38, 1, 'A-38', 'available'),
    (39, 1, 'A-39', 'available'),
    (40, 1, 'A-40', 'available'),
    (41, 1, 'A-41', 'available'),
    (42, 1, 'A-42', 'available'),
    (43, 1, 'A-43', 'available'),
    (44, 1, 'A-44', 'available'),
    (45, 1, 'A-45', 'available'),
    (46, 1, 'A-46', 'available'),
    (47, 1, 'A-47', 'available'),
    (48, 1, 'A-48', 'available'),
    (49, 1, 'A-49', 'available');

-- ── Seats: Learning Plaza B — 8 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (50, 2, 'B-01', 'available'),
    (51, 2, 'B-02', 'available'),
    (52, 2, 'B-03', 'occupied'),
    (53, 2, 'B-04', 'available'),
    (54, 2, 'B-05', 'available'),
    (55, 2, 'B-06', 'available'),
    (56, 2, 'B-07', 'available'),
    (57, 2, 'B-08', 'occupied');

-- ── Seats: Computer Area — 6 seats ────────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (58, 3, 'C-01', 'available'),
    (59, 3, 'C-02', 'available'),
    (60, 3, 'C-03', 'occupied'),
    (61, 3, 'C-04', 'available'),
    (62, 3, 'C-05', 'blocked'),
    (63, 3, 'C-06', 'available');

-- ── Seats: Quiet Study Room — 4 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (64, 4, 'Q-01', 'available'),
    (65, 4, 'Q-02', 'available'),
    (66, 4, 'Q-03', 'available'),
    (67, 4, 'Q-04', 'available');
