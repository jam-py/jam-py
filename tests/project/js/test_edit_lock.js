var assert = chai.assert,
    expect = chai.expect;

describe('EditLock', function() {
    let master;
    const params = [
        {master_rec_no: 0, copy_rec_no: 0, master_edit_lock: true, copy_edit_lock: true},
        {master_rec_no: 0, copy_rec_no: 1, master_edit_lock: true, copy_edit_lock: true},
        {master_rec_no: 0, copy_rec_no: 0, master_edit_lock: true, copy_edit_lock: false},
        {master_rec_no: 0, copy_rec_no: 0, master_edit_lock: false, copy_edit_lock: true}
    ]

    beforeEach(function() {
        task.server('prepare_master_details')
        master = task.master.copy()
        master.open();
        for (let i = 0; i < 2; i++) {
            master.append();
            master.val.value = i;
            master.detail1.open();
            for (let j = 0; j < 2; j++) {
                master.detail1.append();
                master.detail1.val.value = j;
                master.detail1.post();
            }
            master.post();
        }
        master.apply();
    });

    describe('test_copy_edit_lock', function () {
        it('Testing edit_lock of copy', function() {
            let copy;
            master.edit_lock = false;
            copy = master.copy();
            assert.equal(copy.edit_lock, false);

            master.edit_lock = true;
            copy = master.copy()
            assert.equal(copy.edit_lock, true);
        });
    });

    describe('test_detail_copy_edit_lock', function () {
        it('Testing edit_lock of copy detail', function() {
            let copy;
            master.detail1.edit_lock = false;
            copy = master.copy();
            assert.equal(copy.detail1.edit_lock, false);

            master.detail1.edit_lock = true;
            copy = master.copy()
            assert.equal(copy.detail1.edit_lock, true);
        });
    });

    describe('test_edit_lock', function () {
        params.forEach(function(param) {
            it('Testing edit_lock' +
                ' master rec_no = ' + param.master_rec_no +
                ' copy rec_no = ' + param.copy_rec_no +
                ' master edit_lock = ' + param.master_edit_lock +
                ' copy edit_lock = ' + param.copy_edit_lock, function() {

                let copy = master.copy();

                master.edit_lock = param.master_edit_lock;
                copy.edit_lock = param.copy_edit_lock;

                master.open();
                copy.open();

                assert.equal(master.rec_count, 2);
                assert.equal(copy.rec_count, 2);

                master.rec_no = param.master_rec_no;
                copy.rec_no = param.copy_rec_no;

                master.edit();
                master.val.value += 1;
                master.post();
                copy.edit();
                copy.val.value += 1;
                copy.post();
                master.apply();
                if (param.master_rec_no === param.copy_rec_no && param.master_edit_lock && param.master_edit_lock === param.copy_edit_lock) {
                    expect(copy.apply).to.throw();
                }
                else {
                    copy.apply();
                }
            });
        });
    });

    describe('test_detail_edit_lock', function () {
        params.forEach(function(param) {
            it('Testing detail edit_lock' +
                ' master detail rec_no = ' + param.master_rec_no +
                ' copy detail rec_no = ' + param.copy_rec_no +
                ' master detail edit_lock = ' + param.master_edit_lock +
                ' copy detail edit_lock = ' + param.copy_edit_lock, function() {

                let copy = master.copy()

                master.edit_lock = false
                copy.edit_lock = false

                master.detail1.edit_lock = param.master_edit_lock;
                copy.detail1.edit_lock = param.copy_edit_lock;

                master.open();
                master.detail1.open();
                copy.open();
                copy.detail1.open();

                assert.equal(master.id.value, copy.id.value);
                assert.equal(master.detail1.rec_count, 2);
                assert.equal(copy.detail1.rec_count, 2);

                master.detail1.rec_no = param.master_rec_no;
                copy.detail1.rec_no = param.copy_rec_no;

                console.log(param.master_rec_no, param.copy_rec_no, master.detail1.id.value, copy.detail1.id.value,
                    master.detail1.edit_lock, copy.detail1.edit_lock
                )


                master.edit();
                master.detail1.edit();
                master.detail1.val.value += 1;
                master.detail1.post();
                master.post();
                copy.edit();
                copy.detail1.edit();
                copy.detail1.val.value += 1;
                copy.detail1.post();
                copy.post();
                master.apply();
                if (param.master_rec_no === param.copy_rec_no && param.master_edit_lock && param.master_edit_lock === param.copy_edit_lock) {
                    expect(copy.apply).to.throw();
                }
                else {
                    copy.apply();
                }
            });
        });
    });
});
