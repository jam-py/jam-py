import pytest
from jam.dataset import Dataset, DatasetEmpty, DatasetInvalidState

@pytest.fixture
def ds():
    dataset = Dataset()
    dataset.item_name = 'test'
    dataset.open(open_empty=True)
    return dataset

class TestDataset:

    def test_open(self, ds):
        assert ds.active == True
        assert ds.rec_count == 0
        assert ds.rec_no == None

    def test_close(self, ds):
        ds.close()
        assert ds.active == False

    def test_append(self, ds):
        ds.append()
        assert ds.rec_count == 1
        assert ds.rec_no == 0

    def test_insert(self, ds):
        ds.insert()
        assert ds.rec_count == 1
        assert ds.rec_no == 0

    def test_cancel(self, ds):
        ds.append()
        ds.cancel()
        assert ds.rec_count == 0
        assert ds.rec_no == None

    def test_delete(self, ds):
        ds.append()
        ds.post()
        ds.delete()
        assert ds.rec_count == 0
        assert ds.rec_no == None
        with pytest.raises(DatasetEmpty):
            ds.delete()

    def test_post(self, ds):
        ds.append()
        ds.post()
        assert ds.rec_count == 1
        assert ds.rec_no == 0
        with pytest.raises(DatasetInvalidState):
            ds.post()

    def test_ds_records(self, ds):
        ds.append()
        ds.post()
        assert ds.rec_count == 1
        assert ds.rec_no == 0

        ds.insert()
        ds.post()
        assert ds.rec_count == 2
        assert ds.rec_no == 0

        ds.append()
        ds.post()
        assert ds.rec_count == 3
        assert ds.rec_no == 2

        ds.append()
        ds.cancel()
        assert ds.rec_count == 3
        assert ds.rec_no == 2

        ds.delete()
        assert ds.rec_count == 2
        assert ds.rec_no == 1

        ds.delete()
        assert ds.rec_count == 1
        assert ds.rec_no == 0

        ds.delete()
        assert ds.rec_count == 0
        assert ds.rec_no == None

    def test_eof_bof(self, ds):
        assert ds.bof() == True
        assert ds.eof() == True
        assert ds.rec_count == 0
        assert ds.rec_no == None

        for i in range(2):
            ds.append()
            ds.post()
        assert ds.bof() == False
        assert ds.eof() == False
        assert ds.rec_count == 2
        assert ds.rec_no == 1

        ds.first()
        assert ds.bof() == False
        assert ds.eof() == False
        assert ds.rec_no == 0

        ds.prior()
        assert ds.bof() == True
        assert ds.eof() == False
        assert ds.rec_no == 0

        ds.last()
        assert ds.bof() == False
        assert ds.eof() == False
        assert ds.rec_no == 1

        ds.next()
        assert ds.bof() == False
        assert ds.eof() == True
        assert ds.rec_no == 1

        ds.prior()
        assert ds.bof() == False
        assert ds.eof() == False
        assert ds.rec_no == 0

    def test_while(self, ds):
        for i in range(3):
            ds.append()
            ds.post()

        ds.first()
        assert ds.rec_no == 0
        i = 0
        while not ds.eof():
            assert ds.rec_no == i
            ds.next()
            i += 1
        assert ds.rec_no == 2

        ds.last()
        assert ds.rec_no == 2
        i = 2
        while not ds.bof():
            assert ds.rec_no == i
            ds.prior()
            i -= 1
        assert ds.rec_no == 0

    def test_for(self, ds):
        for i in range(3):
            ds.append()
            ds.post()

        for i, d in enumerate(ds):
            assert ds.rec_no == i
        assert ds.rec_no == 2

    def test_rec_no(self, ds):
        for i in range(2):
            ds.append()
            ds.post()
        ds.rec_no = 0
        assert ds.rec_no == 0
        ds.rec_no = 1
        assert ds.rec_no == 1
