import pytest

@pytest.fixture
def master(task):
    master = task.master.copy()
    master.empty()
    detail1 = task.detail1.copy()
    detail1.empty()
    master.open()
    for i in range(2):
        master.append()
        master.val.value = i
        master.detail1.open()
        for j in range(2):
            master.detail1.append()
            master.detail1.val.value = j
            master.detail1.post()
        master.post()
    master.apply()
    return task.master.copy()

class TestEditLock:

    def test_copy_edit_lock(self, master):
        master.edit_lock = False
        copy = master.copy()
        assert not copy.edit_lock

        master.edit_lock = True
        copy = master.copy()
        assert copy.edit_lock

    def test_detail_copy_edit_lock(self, master):
        master.detail1.edit_lock = False
        copy = master.copy()
        assert not copy.detail1.edit_lock

        master.detail1.edit_lock = True
        copy = master.copy()
        assert copy.detail1.edit_lock

    @pytest.mark.parametrize(('master_rec_no, copy_rec_no, master_edit_lock, copy_edit_lock'), [
        (0, 0, True, True),
        (0, 1, True, True),
        (0, 0, True, False),
        (0, 0, False, True)
    ])

    def test_edit_lock(self, master, master_rec_no, copy_rec_no, master_edit_lock, copy_edit_lock):
        copy = master.copy()

        master.edit_lock = master_edit_lock
        copy.edit_lock = copy_edit_lock

        master.open()
        copy.open()

        assert master.rec_count == 2
        assert copy.rec_count == 2

        master.rec_no = master_rec_no
        copy.rec_no = copy_rec_no

        master.edit()
        master.val.value += 1
        master.post()
        copy.edit()
        copy.val.value += 1
        copy.post()
        master.apply()
        if master_rec_no == copy_rec_no and master_edit_lock and master_edit_lock == copy_edit_lock:
            with pytest.raises(Exception):
                copy.apply()
        else:
            copy.apply()

    @pytest.mark.parametrize(('master_rec_no, copy_rec_no, master_edit_lock, copy_edit_lock'), [
        (0, 0, True, True),
        (0, 1, True, True),
        (0, 0, True, False),
        (0, 0, False, True)
    ])

    def test_detail_edit_lock(self, master, master_rec_no, copy_rec_no, master_edit_lock, copy_edit_lock):
        copy = master.copy()

        master.edit_lock = False
        copy.edit_lock = False

        master.detail1.edit_lock = master_edit_lock
        copy.detail1.edit_lock = copy_edit_lock

        master.open()
        master.detail1.open()
        copy.open()
        copy.detail1.open()

        master.detail1.rec_no = master_rec_no
        copy.detail1.rec_no = copy_rec_no

        master.edit()
        master.detail1.edit()
        master.detail1.val.value += 1
        master.detail1.post()
        master.post()
        copy.edit()
        copy.detail1.edit()
        copy.detail1.val.value += 1
        copy.detail1.post()
        copy.post()
        master.apply()
        if master_rec_no == copy_rec_no and master_edit_lock and master_edit_lock == copy_edit_lock:
            with pytest.raises(Exception):
                copy.apply()
        else:
            copy.apply()

