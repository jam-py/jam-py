import pytest

@pytest.fixture
def master(task):
    master = task.master.copy()
    master.empty()
    detail1 = task.detail1.copy()
    detail1.empty()
    detail2 = task.detail2.copy()
    detail2.empty()
    return master

@pytest.fixture
def master2(task):
    master = task.master.copy()
    master.empty()
    detail1 = task.detail1.copy()
    detail1.empty()
    detail2 = task.detail2.copy()
    detail2.empty()
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

class TestDetails:

    def test_master(self, master):
        counter1 = 0
        master.open()
        assert master.rec_count == 0
        for i in range(10):
            master.append()
            master.val.value = i
            master.post()
            counter1 += i
        master.apply()
        master.open()
        counter2 = 0
        for m in master:
            counter2 += master.val.value
        assert master.rec_count == 10
        assert counter1 == counter2

    def test_master_modified(self, master):
        master.open()
        assert master.rec_count == 0
        for i in range(10):
            master.append()
            master.val.value = i
            master.post()
        master.apply()
        counter1 = 0
        master.open()
        while not master.eof():
            if master.id.value % 3 == 0:
                master.delete()
            elif master.id.value % 3 == 1:
                counter1 += master.val.value
                master.edit()
                master.val.value += 1
                master.cancel()
                master.next()
            else:
                master.edit()
                master.val.value += 1
                counter1 += master.val.value
                master.post()

                master.edit()
                master.val.value += 1
                master.cancel()

                master.next()
        master.apply()
        counter2 = 0
        master.open()
        for m in master:
            counter2 += master.val.value
        assert counter1 == counter2

    def test_detail_modified(self, master):
        counter1 = 0
        counter2 = 0
        master.open()
        assert master.rec_count == 0
        for i in range(10):
            master.append()
            master.val.value = i
            master.detail1.open()
            for j in range(i):
                master.detail1.append()
                master.detail1.val.value = j
                master.detail1.post()
                counter2 += j
            master.post()
            counter1 += i
        master.apply()
        master.open()
        counter3 = 0
        counter4 = 0
        for m in master:
            counter3 += master.val.value
            master.detail1.open()
            assert master.detail1.rec_count == m.val.value
            for d in master.detail1:
                counter4 += master.detail1.val.value
        assert master.rec_count == 10
        assert counter1 == counter3
        assert counter2 == counter4

        counter1 = 0
        for m in master:
            m.edit()
            m.detail1.open()
            while not m.detail1.eof():
                if m.detail1.id.value % 3 == 0:
                    m.detail1.delete()
                elif m.detail1.id.value % 3 == 1:
                    counter1 += m.detail1.val.value
                    m.detail1.edit()
                    m.detail1.val.value += 1
                    m.detail1.cancel()
                    m.detail1.next()
                else:
                    m.detail1.edit()
                    m.detail1.val.value += 1
                    m.detail1.cancel()

                    m.detail1.edit()
                    m.detail1.val.value += 1
                    counter1 += m.detail1.val.value
                    m.detail1.post()

                    m.detail1.edit()
                    m.detail1.val.value += 1
                    m.detail1.cancel()

                    m.detail1.next()
            m.post()
        master.apply()
        master.open()
        counter2 = 0
        for m in master:
            m.detail1.open()
            for d in m.detail1:
                counter2 += m.detail1.val.value
        assert counter1 == counter2

    def test_master_detail_detail(self, master):
        counter1 = 0
        counter2 = 0
        counter3 = 0
        master.open()
        assert master.rec_count == 0
        for i in range(10):
            master.append()
            master.val.value = i
            master.detail1.open()
            for j in range(i):
                master.detail1.append()
                master.detail1.val.value = j
                master.detail1.detail2.open()
                for k in range(j):
                    master.detail1.detail2.append()
                    master.detail1.detail2.val.value = k
                    master.detail1.detail2.post()
                    counter3 += k
                master.detail1.post()
                counter2 += j
            master.post()
            counter1 += i
        master.apply()
        master.open()
        counter4 = 0
        counter5 = 0
        counter6 = 0
        for m in master:
            counter4 += m.val.value
            m.detail1.open()
            assert m.detail1.rec_count == m.val.value
            for d in m.detail1:
                counter5 += d.val.value
                m.detail1.detail2.open()
                assert m.detail1.detail2.rec_count == m.detail1.val.value
                for d2 in m.detail1.detail2:
                    counter6 += d2.val.value
        assert m.rec_count == 10
        assert counter1 == counter4
        assert counter2 == counter5
        assert counter3 == counter6

    def test_master_detail_detail_on_apply(self, master):

        def do_on_apply(item, delta, params, connection):
            for d in delta:
                d.edit()
                d.val.value += 1
                for d1 in d.detail1:
                    d1.edit()
                    d1.val.value += 2
                    for d2 in d1.detail2:
                        d2.edit()
                        d2.val.value += 3
                        d2.post()
                    d1.post()
                d.post()

        counter1 = 0
        counter2 = 0
        counter3 = 0
        master.on_apply = do_on_apply
        master.open()
        assert master.rec_count == 0
        for i in range(4):
            master.append()
            master.val.value = i
            master.detail1.open()
            for j in range(i):
                master.detail1.append()
                master.detail1.val.value = j
                master.detail1.detail2.open()
                for k in range(j):
                    master.detail1.detail2.append()
                    master.detail1.detail2.val.value = k
                    master.detail1.detail2.post()
                    counter3 += k + 3
                master.detail1.post()
                counter2 += j + 2
            master.post()
            counter1 += i + 1
        master.apply()
        master.open()
        counter4 = 0
        counter5 = 0
        counter6 = 0
        for m in master:
            counter4 += master.val.value
            master.detail1.open()
            for d in master.detail1:
                counter5 += d.val.value
                master.detail1.detail2.open()
                for d2 in master.detail1.detail2:
                    counter6 += d2.val.value
        assert counter1 == counter4
        assert counter2 == counter5
        assert counter3 == counter6

    def test_log_changes(self, master):
        counter1 = 0
        counter2 = 0
        master.log_changes = True
        master.open()
        assert master.rec_count == 0
        for i in range(10):
            master.append()
            master.val.value = i
            master.post()
            counter1 += i
        master.log_changes = False
        for i in range(10):
            master.append()
            master.val.value = i
            master.post()
        assert master.rec_count == 20
        master.apply()
        master.open()
        for m in master:
            counter2 += master.val.value
        assert master.rec_count == 10
        assert counter1 == counter2
