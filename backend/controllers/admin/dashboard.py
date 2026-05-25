"""Admin dashboard widget data: KPIs, trend charts, zone summaries, alerts."""
from datetime import date, datetime, timedelta, timezone

from db import query_db
from controllers.seats import get_zones_with_seats

from ._common import DB_DATETIME_FORMAT, LOCAL_TZ


def _format_relative_timestamp(utc_str):
    """Convert a UTC timestamp string from SQLite ('YYYY-MM-DD HH:MM:SS') into
    a human-friendly Asia/Taipei string ("just now", "5 min ago",
    "08:07 today", "yesterday 21:14", "Apr 23 · 14:20")."""
    if not utc_str:
        return ''
    try:
        dt_utc = datetime.strptime(utc_str, DB_DATETIME_FORMAT).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return utc_str

    dt_local = dt_utc.astimezone(LOCAL_TZ)
    now_local = datetime.now(LOCAL_TZ)
    delta_sec = (now_local - dt_local).total_seconds()

    if delta_sec < 45:
        return 'just now'
    if delta_sec < 3600:
        return f'{int(delta_sec // 60)} min ago'

    day_offset = (now_local.date() - dt_local.date()).days
    if day_offset == 0:
        return dt_local.strftime('%H:%M today')
    if day_offset == 1:
        return dt_local.strftime('yesterday %H:%M')
    if day_offset < 7:
        return dt_local.strftime('%a %H:%M')
    return dt_local.strftime('%b %d · %H:%M')


def get_dashboard_data():
    """Return zones list and seat summary stats for the admin dashboard."""
    zones = get_zones_with_seats()
    # One query instead of looping over zones — much faster with many zones.
    stats = query_db(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = "blocked" THEN 1 ELSE 0 END) AS blocked
           FROM seats''',
        one=True
    )
    total_seats   = stats['total']   or 0
    blocked_seats = stats['blocked'] or 0
    return zones, total_seats, blocked_seats


def get_admin_kpis():
    """Compute today's live KPIs for the admin dashboard.

    Returns a dict with: occupancy_pct, occupied, usable_total, bookings_today,
    bookings_delta (vs yesterday), no_show_today, no_show_delta, active_now,
    peak_hour (HH:MM string or None).
    """
    now = datetime.now()
    today = now.date()
    yesterday = today - timedelta(days=1)
    today_iso     = today.strftime('%Y-%m-%d')
    yesterday_iso = yesterday.strftime('%Y-%m-%d')
    now_text  = now.strftime(DB_DATETIME_FORMAT)

    seats = query_db(
        '''SELECT COUNT(*) AS total,
                  SUM(CASE WHEN status = "blocked"  THEN 1 ELSE 0 END) AS blocked,
                  SUM(CASE WHEN status = "occupied" THEN 1 ELSE 0 END) AS occupied
           FROM seats''',
        one=True,
    )
    total    = seats['total']    or 0
    blocked  = seats['blocked']  or 0
    occupied = seats['occupied'] or 0
    usable   = total - blocked
    occupancy_pct = round(100 * occupied / usable) if usable > 0 else 0

    def _count(query, params):
        row = query_db(query, params, one=True)
        return (row['c'] if row else 0) or 0

    bookings_today = _count(
        "SELECT COUNT(*) AS c FROM reservations WHERE startTime BETWEEN ? AND ?",
        (f'{today_iso} 00:00:00',     f'{today_iso} 23:59:59'),
    )
    bookings_yest = _count(
        "SELECT COUNT(*) AS c FROM reservations WHERE startTime BETWEEN ? AND ?",
        (f'{yesterday_iso} 00:00:00', f'{yesterday_iso} 23:59:59'),
    )
    no_show_today = _count(
        "SELECT COUNT(*) AS c FROM reservations WHERE status = 'no_show' AND startTime BETWEEN ? AND ?",
        (f'{today_iso} 00:00:00',     f'{today_iso} 23:59:59'),
    )
    no_show_yest = _count(
        "SELECT COUNT(*) AS c FROM reservations WHERE status = 'no_show' AND startTime BETWEEN ? AND ?",
        (f'{yesterday_iso} 00:00:00', f'{yesterday_iso} 23:59:59'),
    )
    active_now = _count(
        "SELECT COUNT(*) AS c FROM reservations WHERE status = 'active' AND startTime <= ? AND endTime > ?",
        (now_text, now_text),
    )

    # Peak hour: histogram of concurrent reservations today.
    rows = query_db(
        "SELECT startTime, endTime FROM reservations WHERE startTime BETWEEN ? AND ?",
        (f'{today_iso} 00:00:00', f'{today_iso} 23:59:59'),
    )
    counts = [0] * 24
    for r in rows:
        s_dt = datetime.strptime(r['startTime'], DB_DATETIME_FORMAT)
        e_dt = datetime.strptime(r['endTime'],   DB_DATETIME_FORMAT)
        # Count the hours the reservation covers (inclusive of start, exclusive of end's whole hour).
        for h in range(s_dt.hour, min(e_dt.hour + (1 if e_dt.minute > 0 else 0), 24)):
            counts[h] += 1
    peak_hour = max(range(24), key=lambda h: counts[h]) if any(counts) else None

    return {
        'occupancy_pct':   occupancy_pct,
        'occupied':        occupied,
        'usable_total':    usable,
        'bookings_today':  bookings_today,
        'bookings_delta':  bookings_today - bookings_yest,
        'no_show_today':   no_show_today,
        'no_show_delta':   no_show_today - no_show_yest,
        'active_now':      active_now,
        'peak_hour':       f'{peak_hour:02d}:00' if peak_hour is not None else None,
    }


def get_hourly_bookings(hours=24):
    """Concurrent reservations per hour over the last `hours` hours.

    Returns a list aligned with Chart.js's expected shape:
        [{'label': '14:00', 'count': N}, ...]
    """
    now = datetime.now()
    start = now - timedelta(hours=hours)

    rows = query_db(
        """
        SELECT startTime, endTime FROM reservations
        WHERE endTime > ? AND startTime < ?
        AND status IN ('upcoming', 'active', 'completed', 'no_show')
        """,
        (start.strftime(DB_DATETIME_FORMAT), now.strftime(DB_DATETIME_FORMAT)),
    )

    parsed = [
        (datetime.strptime(r['startTime'], DB_DATETIME_FORMAT),
         datetime.strptime(r['endTime'],   DB_DATETIME_FORMAT))
        for r in rows
    ]

    buckets = []
    for i in range(hours):
        b_start = (start + timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        b_end   = b_start + timedelta(hours=1)
        count = sum(1 for (s, e) in parsed if s < b_end and e > b_start)
        buckets.append({'label': b_start.strftime('%H:00'), 'count': count})
    return buckets


def get_metric_series(metric, days=7):
    """Daily count for a single KPI metric over the trailing `days` days.

    `metric` ∈ ('bookings', 'no_shows'). Returns [{'label': 'Mon', 'count': N}, ...].
    """
    if metric not in ('bookings', 'no_shows'):
        raise ValueError(f'Unknown metric: {metric}')

    sql_filter = "AND status = 'no_show'" if metric == 'no_shows' else ''
    today = date.today()
    series = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        row = query_db(
            f"SELECT COUNT(*) AS c FROM reservations WHERE startTime BETWEEN ? AND ? {sql_filter}",
            (f'{day.isoformat()} 00:00:00', f'{day.isoformat()} 23:59:59'),
            one=True,
        )
        series.append({
            'label': day.strftime('%a'),
            'count': (row['c'] if row else 0) or 0,
        })
    return series


_PEAK_BUCKETS = (
    ('Morning (08–11)',  range(8, 12)),
    ('Midday (12–14)',   range(12, 15)),
    ('Afternoon (15–17)', range(15, 18)),
    ('Evening (18–20)',  range(18, 21)),
)


def get_peak_hour_forecast(days=30):
    """Histogram of reservations by time-of-day bucket over the last `days` days.

    Returns an OrderedDict-like list of (bucket_label, count) preserving the
    morning→evening order — friendly for a ring/doughnut chart.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat() + ' 00:00:00'
    rows = query_db(
        "SELECT startTime FROM reservations WHERE startTime >= ?",
        (cutoff,),
    )

    counts = {label: 0 for label, _ in _PEAK_BUCKETS}
    for r in rows:
        hour = datetime.strptime(r['startTime'], DB_DATETIME_FORMAT).hour
        for label, bucket in _PEAK_BUCKETS:
            if hour in bucket:
                counts[label] += 1
                break
    return [{'label': label, 'count': counts[label]} for label, _ in _PEAK_BUCKETS]


def get_zone_summaries(days=30, top_n=3):
    """Per-zone usage summary for the dashboard sidecar.

    Returns the data the redesigned ZoneCard needs — live availability plus
    the top-N most-booked named seats over the last `days` days. The named
    seats (e.g. "A-04") give admins something concrete to act on, whereas
    an anonymous density heatmap requires knowing the floor plan to interpret.

    Shape:
        [{
            'zoneId', 'name', 'location', 'total', 'blocked',
            'available_now', 'tier',                     # 'high' | 'average' | 'quiet'
            'top_seats': [{'deskNo', 'uses'}, ...],      # most-booked first, length ≤ top_n
            'total_bookings': N,                         # in the window
        }, ...]
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat() + ' 00:00:00'
    zones = query_db('SELECT zoneId, name, location FROM zones ORDER BY zoneId')

    result = []
    for z in zones:
        seats = query_db(
            """
            SELECT s.seatId, s.deskNo, s.status,
                   (SELECT COUNT(*) FROM reservations r
                    WHERE r.seatId = s.seatId AND r.startTime >= ?) AS uses
            FROM seats s
            WHERE s.zoneId = ?
            ORDER BY s.deskNo
            """,
            (cutoff, z['zoneId']),
        )

        seats_list  = [dict(s) for s in seats]
        total       = len(seats_list)
        blocked     = sum(1 for s in seats_list if s['status'] == 'blocked')
        available   = sum(1 for s in seats_list if s['status'] == 'available')
        active_uses = [s['uses'] or 0 for s in seats_list if s['status'] != 'blocked']
        total_bookings = sum(active_uses)

        # Tier classification by mean usage among non-blocked seats. Thresholds
        # are intentionally permissive at the low end since libraries are quiet
        # most of the time — we don't want every zone screaming "high demand".
        usable_count = total - blocked
        avg_per_seat = (total_bookings / usable_count) if usable_count else 0
        if   avg_per_seat >= 8:   tier = 'high'
        elif avg_per_seat >= 2:   tier = 'average'
        else:                     tier = 'quiet'

        # Most-booked seats, excluding blocked ones.
        top_seats = sorted(
            (s for s in seats_list if s['status'] != 'blocked' and (s['uses'] or 0) > 0),
            key=lambda s: s['uses'] or 0,
            reverse=True,
        )[:top_n]
        top_seats = [{'deskNo': s['deskNo'], 'uses': s['uses'] or 0} for s in top_seats]

        result.append({
            'zoneId':         z['zoneId'],
            'name':           z['name'],
            'location':       z['location'],
            'total':          total,
            'blocked':        blocked,
            'available_now':  available,
            'tier':           tier,
            'top_seats':      top_seats,
            'total_bookings': total_bookings,
        })

    return result


def recent_admin_actions(limit=10):
    """Latest admin_action_logs rows with human-friendly target labels.

    Returns [{'actor', 'actor_id', 'actionType', 'target', 'timestamp', 'timestamp_utc'}, ...].
    """
    rows = query_db(
        """
        SELECT a.actionId, a.userId, u.uname AS actor, a.actionType,
               a.seatId, s.deskNo, z.name AS zoneName,
               a.penaltyId, a.timeStamp
        FROM admin_action_logs a
        LEFT JOIN users u ON u.uId    = a.userId
        LEFT JOIN seats s ON s.seatId = a.seatId
        LEFT JOIN zones z ON z.zoneId = s.zoneId
        ORDER BY a.actionId DESC
        LIMIT ?
        """,
        (limit,),
    )

    actions = []
    for r in rows:
        if r['seatId'] is not None and r['deskNo']:
            target = f"{r['zoneName']} · {r['deskNo']}"
        elif r['penaltyId'] is not None:
            target = f"penalty #{r['penaltyId']}"
        else:
            target = ''
        actions.append({
            'actor':          r['actor'] or r['userId'],
            'actor_id':       r['userId'],
            'actionType':     r['actionType'],
            'target':         target,
            'timestamp':      _format_relative_timestamp(r['timeStamp']),
            'timestamp_utc':  r['timeStamp'],
        })
    return actions


def derive_alerts(kpis):
    """Rule-based, non-IoT suggestions derived from current KPIs.

    Returns a list of dicts: {'title', 'body', 'severity'} where severity is
    one of ('info', 'warning', 'critical'). Always returns at least one entry
    so the dashboard never shows an empty alert slot.
    """
    alerts = []
    usable = kpis.get('usable_total', 0) or 0
    active = kpis.get('active_now', 0) or 0

    if kpis.get('occupancy_pct', 0) >= 85:
        alerts.append({
            'title':    'High demand right now',
            'body':     f"{kpis['occupancy_pct']}% of usable seats are occupied. "
                        "Consider opening overflow study rooms before peak hour.",
            'severity': 'warning',
        })
    if kpis.get('no_show_today', 0) > 5:
        alerts.append({
            'title':    'Spike in no-shows today',
            'body':     f"{kpis['no_show_today']} no-shows logged today. "
                        "Review penalty thresholds or check-in flow.",
            'severity': 'warning',
        })
    if usable > 0 and active >= usable * 0.9:
        alerts.append({
            'title':    'Library nearing capacity',
            'body':     f"{active} of {usable} usable seats are active. Free seats are scarce.",
            'severity': 'critical',
        })

    if not alerts:
        alerts.append({
            'title':    "Nothing needs your attention",
            'body':     "We're watching occupancy, no-shows, and capacity. "
                        "Anything unusual will show up here as it happens.",
            'severity': 'info',
        })
    return alerts
