
def test_app(app, admin):
    assert app.admin == admin

def test_admin(admin):
    assert admin.item_name == 'admin'

def test_task(task):
    assert task.item_name == 'test'
