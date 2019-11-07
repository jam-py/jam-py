var assert = chai.assert;

describe('Details', function() {
    var master;

    beforeEach(function() {
        task.server('prepare_master_details')
        master = task.master.copy()
    });

    describe('test_master', function () {
        it('Testing master', function() {
            let counter1 = 0;
            master.open();
            assert.equal(master.rec_count, 0);
            for (let i = 0; i < 10; i++) {
                master.append();
                master.val.value = i;
                master.post();
                counter1 += i;
            }
            master.apply();
            master.open();
            let counter2 = 0;
            master.each(function(m) {
                counter2 += m.val.value;
            });
            assert.equal(master.rec_count, 10);
            assert.equal(counter1, counter2);
        });
    });

    describe('test_master_modified', function () {
        it('Testing master modified', function() {
            master.open();
            assert.equal(master.rec_count, 0);
            for (let i = 0; i < 10; i++) {
                master.append();
                master.val.value = i;
                master.post();
            }
            master.apply();
            let counter1 = 0;
            master.open();
            master.first();
            while (!master.eof()) {
                if (master.id.value % 3 === 0) {
                    master.delete();
                }
                else if (master.id.value % 3 === 1) {
                    counter1 += master.val.value;
                    master.edit();
                    master.val.value += 1;
                    master.cancel();
                    master.next()
                }
                else {
                    master.edit();
                    master.val.value += 1;
                    counter1 += master.val.value;
                    master.post();
                    master.next();
                }
            }
            let counter2 = 0;
            master.each(function(m) {
                counter2 += m.val.value;
            });
            assert.equal(counter1, counter2);
            master.apply();
            master.open();
            let counter3 = 0;
            master.each(function(m) {
                counter3 += m.val.value;
            });
            assert.equal(counter2, counter3);
        });
    });

    describe('test_detail_modified', function () {
        it('Testing detail modified', function() {
            let counter1 = 0,
                counter2 = 0;
            master.open();
            assert.equal(master.rec_count, 0);
            for (let i = 0; i < 10; i++) {
                master.append()
                master.val.value = i
                master.detail1.open()
                for (let j = 0; j < i; j++) {
                    master.detail1.append();
                    master.detail1.val.value = j;
                    master.detail1.post();
                    counter2 += j;
                }
                master.post();
                counter1 += i;
            }

            master.apply();
            //~ master.open()
            let counter3 = 0,
                counter4 = 0;
            master.each(function (m) {
                counter3 += m.val.value;
                m.detail1.open()
                assert.equal(m.detail1.rec_count, m.val.value);
                m.detail1.each(function (d) {
                    counter4 += master.detail1.val.value;
                });
            });
            assert.equal(master.rec_count, 10);
            assert.equal(counter1, counter3);
            assert.equal(counter2, counter4);

            counter1 = 0;
            master.each(function(m) {
                m.edit();
                m.detail1.open();
                while (!m.detail1.eof()) {
                    if (m.detail1.id.value % 3 === 0) {
                        m.detail1.delete();
                    }
                    else if (m.detail1.id.value % 3 === 1) {
                        counter1 += m.detail1.val.value;
                        m.detail1.edit();
                        m.detail1.val.value += 1;
                        m.detail1.cancel();
                        m.detail1.next();
                    }
                    else {
                        m.detail1.edit();
                        m.detail1.val.value += 1;
                        counter1 += m.detail1.val.value;
                        m.detail1.post();
                        m.detail1.next();
                    }
                }
                m.post();
            });
            master.apply();
            master.open();
            counter2 = 0
            master.each(function(m) {
                m.detail1.open();
                m.detail1.each(function(d) {
                    counter2 += m.detail1.val.value;
                });
            });
            assert.equal(counter1, counter2);
        });
    });

    describe('test_master_detail_detail', function () {
        it('Testing master detail detail', function() {
            let counter1 = 0,
                counter2 = 0,
                counter3 = 0;
            master.open();
            assert.equal(master.rec_count, 0);
            for (let i = 0; i < 10; i++) {
                master.append();
                master.val.value = i;
                master.detail1.open();
                for (let j = 0; j < i; j++) {
                    master.detail1.append();
                    master.detail1.val.value = j;
                    master.detail1.detail2.open();
                    for (let k = 0; k < j; k++) {
                        master.detail1.detail2.append();
                        master.detail1.detail2.val.value = k;
                        master.detail1.detail2.post();
                        counter3 += k;
                    }
                    master.detail1.post();
                    counter2 += j;
                }
                master.post();
                counter1 += i;
            }
            master.apply()
            master.open()
            let counter4 = 0,
                counter5 = 0,
                counter6 = 0;
            master.each(function(m) {
                counter4 += m.val.value;
                m.detail1.open();
                assert.equal(m.detail1.rec_count, m.val.value);
                m.detail1.each(function(d) {
                    counter5 += d.val.value
                    m.detail1.detail2.open()
                    assert.equal(m.detail1.detail2.rec_count, m.detail1.val.value);
                    m.detail1.detail2.each(function(d2) {
                        counter6 += d2.val.value
                    });
                });
            });
            assert.equal(master.rec_count, 10);
            assert.equal(counter1, counter4);
            assert.equal(counter2, counter5);
            assert.equal(counter3, counter6);
        });
    });

    describe('test_logging', function () {
        it('Testing logging', function() {
            let counter1 = 0;
            master.open();
            assert.equal(master.rec_count, 0);
            for (let i = 0; i < 10; i++) {
                master.append();
                master.val.value = i;
                master.post();
                counter1 += i;
            }
            master.log_changes = false;
            for (let i = 0; i < 10; i++) {
                master.append();
                master.val.value = i;
                master.post();
            }
            assert.equal(master.rec_count, 20);
            master.apply();
            master.open();
            let counter2 = 0;
            master.each(function(m) {
                counter2 += m.val.value;
            });
            assert.equal(master.rec_count, 10);
            assert.equal(counter1, counter2);
        });
    });
});


