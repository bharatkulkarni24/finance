import pytest

from core.models.member import (
    get_all_members, create_member, find_member_by_name,
    get_member, update_member,
)
from core.database import get_conn, row_to_dict


# ─── Zombies: Simple ──────────────────────────────────────────────────────────

class TestMemberSimple:
    def test_create_member(self, setup_db):
        m = create_member('Test User')
        assert m['name'] == 'Test User'
        assert m['deposit_amount'] == 25000
        assert m['is_admin'] == 0

    def test_get_all_members_empty_after_clean(self, setup_db):
        members = get_all_members()
        assert isinstance(members, list)


# ─── Zombies: Zero ────────────────────────────────────────────────────────────

class TestMemberZero:
    def test_empty_name_still_creates(self, setup_db):
        m = create_member('')
        assert m['name'] == ''

    def test_find_nonexistent_member(self):
        m = find_member_by_name('Nonexistent Person')
        assert m is None

    def test_get_nonexistent_member(self):
        m = get_member(99999)
        assert m is None

    def test_get_nonexistent_member_full(self):
        m = get_member(99999, full=True)
        assert m is None

    def test_update_nonexistent_member(self):
        result = update_member(99999, phone='123')
        assert result is None

    def test_zero_members_after_clean(self, setup_db):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM members')
        conn.commit()
        conn.close()
        members = get_all_members()
        assert len(members) == 0


# ─── Zombies: One ─────────────────────────────────────────────────────────────

class TestMemberOne:
    def test_create_one_member(self, setup_db):
        m = create_member('Alice', phone='9999999999', is_admin=1)
        assert m['id'] is not None
        assert m['name'] == 'Alice'
        assert m['phone'] == '9999999999'
        assert m['is_admin'] == 1

    def test_find_one_member_by_name(self, setup_db):
        create_member('Bob')
        found = find_member_by_name('Bob')
        assert found is not None
        assert found['name'] == 'Bob'

    def test_find_case_insensitive(self, setup_db):
        create_member('Charlie')
        found = find_member_by_name('charlie')
        assert found is not None

    def test_get_one_member(self, setup_db):
        m = create_member('Dave')
        fetched = get_member(m['id'])
        assert fetched['name'] == 'Dave'

    def test_get_one_member_full_returns_relations(self, setup_db):
        m = create_member('Eve')
        full = get_member(m['id'], full=True)
        assert 'contributions' in full
        assert 'loans' in full
        assert 'payments' in full
        assert 'dues' in full
        assert 'payment_requests' in full


# ─── Zombies: Many ────────────────────────────────────────────────────────────

class TestMemberMany:
    def test_create_multiple_members(self, setup_db):
        names = ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve']
        for name in names:
            create_member(name)
        all_m = get_all_members()
        assert len(all_m) == len(names)
        assert all(m['name'] in names for m in all_m)

    def test_find_among_many(self, setup_db):
        for name in ['Alice', 'Bob', 'Charlie']:
            create_member(name)
        found = find_member_by_name('Bob')
        assert found['name'] == 'Bob'


# ─── Zombies: Boundary ────────────────────────────────────────────────────────

class TestMemberBoundary:
    def test_long_name(self, setup_db):
        long_name = 'A' * 200
        m = create_member(long_name)
        assert m['name'] == long_name

    def test_special_characters_in_name(self, setup_db):
        m = create_member("O'Brien-Smith-Jones")
        assert m['name'] == "O'Brien-Smith-Jones"

    def test_deposit_amount_default(self, setup_db):
        m = create_member('Test')
        assert m['deposit_amount'] == 25000

    def test_update_phone_only(self, setup_db):
        m = create_member('Update Test')
        updated = update_member(m['id'], phone='9876543210')
        assert updated['phone'] == '9876543210'
        assert updated['name'] == 'Update Test'

    def test_update_all_fields(self, setup_db):
        m = create_member('Full Update')
        updated = update_member(m['id'], phone='1111111111', dob='1990-01-01',
                                address='123 Test St', photo_url='/img/photo.jpg')
        assert updated['phone'] == '1111111111'
        assert updated['dob'] == '1990-01-01'
        assert updated['address'] == '123 Test St'
        assert updated['photo_url'] == '/img/photo.jpg'


# ─── Zombies: Interface ───────────────────────────────────────────────────────

class TestMemberInterface:
    def test_create_adds_initial_contribution(self, setup_db):
        m = create_member('Initial Deposit')
        full = get_member(m['id'], full=True)
        deposits = [c for c in full['contributions'] if c['type'] == 'deposit']
        assert len(deposits) >= 1
        assert deposits[0]['amount'] == 25000

    def test_create_generates_dues(self, setup_db):
        m = create_member('Dues Check')
        full = get_member(m['id'], full=True)
        assert len(full['dues']) > 0

    def test_update_then_get_reflects_changes(self, setup_db):
        m = create_member('Before')
        update_member(m['id'], phone='5555555555')
        fetched = get_member(m['id'])
        assert fetched['phone'] == '5555555555'


# ─── Zombies: Exception ───────────────────────────────────────────────────────

class TestMemberException:
    def test_update_with_no_changes_returns_member(self, setup_db):
        m = create_member('No Change')
        result = update_member(m['id'])
        assert result['name'] == 'No Change'

    def test_create_with_none_name(self, setup_db):
        with pytest.raises(Exception):
            create_member(None)

    def test_get_member_with_zero_id(self):
        m = get_member(0)
        assert m is None

    def test_find_member_empty_string(self):
        found = find_member_by_name('')
        assert found is None
