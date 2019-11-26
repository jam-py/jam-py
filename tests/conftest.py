import pytest
import os
import datetime
from jam.wsgi import create_application

@pytest.fixture(scope="session", autouse=True)
def app(request):
    project_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'project')
    return create_application(project_folder, load_task=True, testing=True)

@pytest.fixture(scope="session", autouse=True)
def admin(app):
    return app.admin

@pytest.fixture(scope="session", autouse=True)
def task(app):
    return app.task

@pytest.fixture(scope="module")
def fields_item(task):
    date = datetime.datetime.strptime('2019-10-30', '%Y-%m-%d').date()
    date_string = '10/30/2019'
    date_time = datetime.datetime.strptime('2019-10-30 10:10:20', '%Y-%m-%d %H:%M:%S')
    datetime_string = '10/30/2019 10:10:20'

    lookup3 = task.lookup3.copy()
    lookup3.empty()
    lookup3.open(open_empty=True)
    for i in range(2):
        val = i + 1
        lookup3.append()
        lookup3.text_field.value = 'lookup3_text' + str(i + 1)
        lookup3.integer_field.value = val;
        lookup3.currency_field.value = 100.001
        lookup3.date_field.value = date
        lookup3.datetime_field.value = date_time
        lookup3.boolean_field.value = bool(i)
        lookup3.lookup_list_field.value = val
        lookup3.keys_field.value = [val, val+1]
        lookup3.image_field.value = 'img%s.jpeg' % val
        lookup3.file_field.value = 'img_%s.jpg?img %s.jpg' % (val, val)
        lookup3.post()
    lookup3.apply()
    lookup3.first()
    assert lookup3.rec_count == 2

    lookup2 = task.lookup2.copy()
    lookup2.empty()
    lookup2.open(open_empty=True)
    for i in range(2):
        lookup2.append()
        lookup2.name.value = 'lookup2_text' + str(i + 1)
        lookup3.rec_no = i
        lookup2.lookup3_text_field.value = lookup3.id.value
        lookup2.post()
    lookup2.apply()
    lookup2.open()

    lookup1 = task.lookup1.copy()
    lookup1.empty()
    lookup1.open(open_empty=True)
    for i in range(2):
        lookup1.append()
        lookup1.name.value = 'lookup1_name' + str(i + 1)
        lookup2.rec_no = i
        lookup1.lookup_field2.value = lookup2.id.value
        lookup1.post()
    lookup1.apply()
    lookup1.last() #!!!!!!!!!!!!!
    assert lookup1.rec_count == 2

    item = task.item.copy()
    item.empty()
    item.open()
    item.append()
    item.lookup1_name_field.value = lookup1.id.value
    item.lookup_list_field.value = 1
    item.post()
    item.apply()
    return item



