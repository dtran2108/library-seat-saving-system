-- seed.sql — Development seed data for the Library Seat Saving System.
--
-- Contains only INSERT OR IGNORE statements with explicit PKs.
-- Idempotent: safe to re-run on an existing database — rows that already
-- exist (matched on PK) are silently skipped.
--
-- Layout reference:
--   Learning Plaza A   : 7 cols → 7 rows × 7 seats each  (49 seats/zone)
--   Learning Plaza B   : 8 cols → 6 rows × 8 seats each  (48 seats/zone)
--   Computer Area      : 3 cols → 2 rows × 3 seats        (6 seats)
--   Quiet Study Room   : 4 cols → 1 row  × 4 seats        (4 seats)
--   Total              : 4 zones, 115 seats

-- ── Zones ─────────────────────────────────────────────────────────────────
INSERT OR IGNORE INTO zones (zoneId, name,               location,    cols, status) VALUES
    (1, 'Learning Plaza A', '1st Floor',  7, 'active'),
    (2, 'Learning Plaza B', '1st Floor',  8, 'active'),
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

-- ── Seats: Learning Plaza B — 48 seats ───────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (50, 2, 'B-01', 'available'),
    (51, 2, 'B-02', 'available'),
    (52, 2, 'B-03', 'available'),
    (53, 2, 'B-04', 'available'),
    (54, 2, 'B-05', 'available'),
    (55, 2, 'B-06', 'available'),
    (56, 2, 'B-07', 'available'),
    (57, 2, 'B-08', 'available'),
    (58, 2, 'B-09', 'available'),
    (59, 2, 'B-10', 'available'),
    (60, 2, 'B-11', 'available'),
    (61, 2, 'B-12', 'available'),
    (62, 2, 'B-13', 'available'),
    (63, 2, 'B-14', 'available'),
    (64, 2, 'B-15', 'available'),
    (65, 2, 'B-16', 'available'),
    (66, 2, 'B-17', 'available'),
    (67, 2, 'B-18', 'available'),
    (68, 2, 'B-19', 'available'),
    (69, 2, 'B-20', 'available'),
    (70, 2, 'B-21', 'available'),
    (71, 2, 'B-22', 'available'),
    (72, 2, 'B-23', 'available'),
    (73, 2, 'B-24', 'available'),
    (74, 2, 'B-25', 'available'),
    (75, 2, 'B-26', 'available'),
    (76, 2, 'B-27', 'available'),
    (77, 2, 'B-28', 'available'),
    (78, 2, 'B-29', 'available'),
    (79, 2, 'B-30', 'available'),
    (80, 2, 'B-31', 'available'),
    (81, 2, 'B-32', 'available'),
    (82, 2, 'B-33', 'available'),
    (83, 2, 'B-34', 'available'),
    (84, 2, 'B-35', 'available'),
    (85, 2, 'B-36', 'available'),
    (86, 2, 'B-37', 'available'),
    (87, 2, 'B-38', 'available'),
    (88, 2, 'B-39', 'available'),
    (89, 2, 'B-40', 'available'),
    (90, 2, 'B-41', 'available'),
    (91, 2, 'B-42', 'available'),
    (92, 2, 'B-43', 'available'),
    (93, 2, 'B-44', 'available'),
    (94, 2, 'B-45', 'available'),
    (95, 2, 'B-46', 'available'),
    (96, 2, 'B-47', 'available'),
    (97, 2, 'B-48', 'available');

-- ── Seats: Computer Area — 6 seats ────────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (98, 3, 'C-01', 'available'),
    (99, 3, 'C-02', 'available'),
    (100, 3, 'C-03', 'occupied'),
    (101, 3, 'C-04', 'available'),
    (102, 3, 'C-05', 'blocked'),
    (103, 3, 'C-06', 'available');

-- ── Seats: Quiet Study Room — 4 seats ─────────────────────────────────────
INSERT OR IGNORE INTO seats (seatId, zoneId, deskNo,  status) VALUES
    (104, 4, 'Q-01', 'available'),
    (105, 4, 'Q-02', 'available'),
    (106, 4, 'Q-03', 'available'),
    (107, 4, 'Q-04', 'available');
