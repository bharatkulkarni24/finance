from datetime import date
import pytest

from core.database import get_conn
from core.models.dues import generate_dues_for_member, get_dues, calculate_due_amount
from core.models.member import create_member, get_member


def _make_member(name='Test'):
    from datetime import datetime
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('INSERT INTO members (name, joined_date, deposit_amount) VALUES (?,?,?)',
                (name, datetime.utcnow().date().isoformat(), 25000))
    mid = cur.lastrowid
    conn.commit()
    conn.close()
    return {'id': mid}


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestDuesSimple:
    def test_generate_dues(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 1, 1), months=3, monthly_amount=500)
        dues = get_dues(m['id'])
        assert len(dues) == 3


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestDuesZero:
    def test_no_dues_for_new_member(self, setup_db):
        m = _make_member()
        dues = get_dues(m['id'])
        assert len(dues) == 0

    def test_calculate_due_no_dues(self, setup_db):
        m = _make_member()
        calc = calculate_due_amount(m['id'], date(2026, 6, 22))
        assert calc['due'] == 0
        assert calc['late_fee'] == 0
        assert calc['total'] == 0

    def test_zero_month_generation(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 1, 1), months=0)
        dues = get_dues(m['id'])
        assert len(dues) == 0

    def test_zero_amount_dues(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 1, 1), months=2, monthly_amount=0)
        dues = get_dues(m['id'])
        assert dues[0]['amount'] == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestDuesOne:
    def test_generate_one_due(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 6, 1), months=1)
        dues = get_dues(m['id'])
        assert len(dues) == 1
        assert dues[0]['amount'] == 500

    def test_calculate_one_due(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 6, 1), months=1)
        calc = calculate_due_amount(m['id'], date(2026, 6, 22))
        assert calc['due'] == 500
        assert calc['late_fee'] > 0


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestDuesMany:
    def test_generate_36_dues(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2025, 4, 1), months=36)
        dues = get_dues(m['id'])
        assert len(dues) == 36
        assert dues[0]['amount'] == 500
        assert dues[-1]['amount'] == 500

    def test_due_date_is_10th_of_month(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2025, 4, 1), months=3)
        dues = get_dues(m['id'])
        for d in dues:
            dt = date.fromisoformat(d['due_date'])
            assert dt.day == 10


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestDuesBoundary:
    def test_due_on_due_date_no_late_fee(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 6, 1), months=1)
        calc = calculate_due_amount(m['id'], date(2026, 6, 10))
        assert calc['due'] == 500
        assert calc['late_fee'] == 0

    def test_due_one_day_late(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 6, 1), months=1)
        calc = calculate_due_amount(m['id'], date(2026, 6, 11))
        assert calc['late_fee'] == 50

    def test_due_30_days_late(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 5, 1), months=1)
        calc = calculate_due_amount(m['id'], date(2026, 6, 10))
        assert calc['late_fee'] == 50 * 31

    def test_year_boundary_due(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2025, 12, 1), months=2)
        dues = get_dues(m['id'])
        assert len(dues) == 2
        assert date.fromisoformat(dues[0]['due_date']).month == 12
        assert date.fromisoformat(dues[1]['due_date']).month == 1


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestDuesInterface:
    def test_create_member_generates_dues(self, setup_db):
        m = create_member('Test')
        full = get_member(m['id'], full=True)
        assert len(full['dues']) >= 1

    def test_calculate_due_ignores_paid(self, setup_db):
        m = _make_member()
        generate_dues_for_member(m['id'], date(2026, 6, 1), months=2)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('UPDATE dues SET paid=1 WHERE id IN (SELECT id FROM dues WHERE member_id=? LIMIT 1)', (m['id'],))
        conn.commit()
        conn.close()
        calc = calculate_due_amount(m['id'], date(2026, 7, 22))
        assert calc['due'] == 500


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestDuesException:
    def test_generate_for_nonexistent_member(self, setup_db):
        generate_dues_for_member(99999, date(2026, 1, 1), months=3)
        dues = get_dues(99999)
        assert len(dues) == 3
