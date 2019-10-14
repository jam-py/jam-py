var assert = chai.assert,
    expect = chai.expect;

describe('Dataset', function() {
    var ds;

    beforeEach(function() {
        ds = new task.Item()
        ds.open({open_empty: true});
    });

    describe('test_open', function () {
        it('Testing open method with open_empty option', function() {
            let counter = 0;
            ds = new task.Item()
            ds.on_before_scroll = function(d) {
                assert.equal(counter, 0);
                counter += 1;
            }
            ds.on_after_scroll = function(d) {
                assert.equal(counter, 1);
            }
            ds.open({open_empty: true});
            assert.equal(ds.active, true);
            assert.equal(ds.rec_count, 0);
            assert.equal(ds.rec_no, null);
        });
    });

    describe('test_close', function () {
        it('Testing close method', function() {
            ds.close()
            assert.equal(ds.active, false);
        });
    });

    describe('test_append', function () {
        it('Testing append method', function() {
            let counter = 0;
            ds.on_before_append = function(d) {
                assert.equal(counter, 0);
                counter += 1;
            }
            ds.on_before_scroll = function(d) {
                assert.equal(counter, 1);
                counter += 1;
            }
            ds.on_after_scroll = function(d) {
                assert.equal(counter, 2);
                counter += 1;
            }
            ds.on_after_append = function(d) {
                assert.equal(counter, 3);
                counter += 1;
            }
            ds.append();
            assert.equal(ds.rec_count, 1);
            assert.equal(ds.rec_no, 0);
        });
    });

    describe('test_insert', function () {
        it('Testing insert method', function() {
            ds.insert();
            assert.equal(ds.rec_count, 1);
            assert.equal(ds.rec_no, 0);
        })
    });

    describe('test_cancel', function () {
        it('Testing cncel method', function() {
            let counter = 0;
            ds.append();
            ds.on_before_cancel = function(d) {
                assert.equal(counter, 0);
                counter += 1;
            }
            ds.on_after_cancel = function(d) {
                assert.equal(counter, 1);
                counter += 1;
            }
            ds.cancel();
            assert.equal(ds.rec_count, 0);
            assert.equal(ds.rec_no, null);
        });
    });

    describe('test_delete', function () {
        it('Testing delete method', function() {
            let counter = 0;
            ds.append();
            ds.post();
            ds.on_before_delete = function(d) {
                assert.equal(counter, 0);
                counter += 1;
            }
            ds.on_before_scroll = function(d) {
                assert.equal(counter, 1);
                counter += 1;
            }
            ds.on_after_scroll = function(d) {
                assert.equal(counter, 2);
                counter += 1;
            }
            ds.on_after_delete = function(d) {
                assert.equal(counter, 3);
                counter += 1;
            }
            ds.delete();
            assert.equal(ds.rec_count, 0);
            assert.equal(ds.rec_no, null);
            expect(ds.delete).to.throw();
        })
    });

    describe('test_post', function () {
        it('Testing post method', function() {
            ds.append();
            ds.post();
            assert.equal(ds.rec_count, 1);
            assert.equal(ds.rec_no, 0);
            expect(ds.post).to.throw();
        });
    });

    describe('test_ds_records', function () {
        it('Testing ds methods', function() {
            ds.append();
            ds.post();
            assert.equal(ds.rec_count, 1);
            assert.equal(ds.rec_no, 0);

            ds.insert();
            ds.post();
            assert.equal(ds.rec_count, 2);
            assert.equal(ds.rec_no, 0);

            ds.append();
            ds.post();
            assert.equal(ds.rec_count, 3);
            assert.equal(ds.rec_no, 2);

            ds.append();
            ds.cancel()
            assert.equal(ds.rec_count, 3);
            assert.equal(ds.rec_no, 2);

            ds.delete()
            assert.equal(ds.rec_count, 2);
            assert.equal(ds.rec_no, 1);

            ds.delete()
            assert.equal(ds.rec_count, 1);
            assert.equal(ds.rec_no, 0);

            ds.delete()
            assert.equal(ds.rec_count, 0);
            assert.equal(ds.rec_no, null);

            expect(ds.delete).to.throw();
        });
    });

    describe('test_eof_bof', function () {
        it('Testing eof, bof method', function() {
            assert.equal(ds.bof(), true);
            assert.equal(ds.eof(), true);
            assert.equal(ds.rec_count, 0);
            assert.equal(ds.rec_no, null);

            for (let i = 0; i < 2; i++) {
                ds.append();
                ds.post();
            }
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_count, 2);
            assert.equal(ds.rec_no, 1);

            ds.first()
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_no, 0);

            ds.prior()
            assert.equal(ds.bof(), true);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_no, 0);

            ds.next()
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_no, 1);

            ds.last()
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_no, 1);

            ds.next()
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), true);
            assert.equal(ds.rec_no, 1);

            ds.prior()
            assert.equal(ds.bof(), false);
            assert.equal(ds.eof(), false);
            assert.equal(ds.rec_no, 0);
        });
    });

    describe('test_while', function () {
        it('Testing while loop', function() {
            for (let i = 0; i < 3; i++) {
                ds.append();
                ds.post();
            }

            ds.first();
            assert.equal(ds.rec_no, 0);
            i = 0
            while(!ds.eof()) {
                assert.equal(ds.rec_no, i);
                ds.next()
                i += 1
            }
            assert.equal(ds.rec_no, 2);

            ds.last()
            assert.equal(ds.rec_no, 2);
            i = 2
            while(!ds.bof()) {
                assert.equal(ds.rec_no, i);
                ds.prior()
                i -= 1
            }
            assert.equal(ds.rec_no, 0);
        });
    });

    describe('test_each', function () {
        it('Testing each method', function() {
            for (let i = 0; i < 3; i++) {
                ds.append();
                ds.post();
            }

            let r = 0
            ds.each(function(ds) {
                assert.equal(ds.rec_no, r);
                r += 1;
            });
            assert.equal(ds.rec_no, 2);
        });
    });

});
