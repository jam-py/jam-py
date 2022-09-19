import os
import zipfile
import json
import datetime

from ..common import consts, to_str

metadata_items = [
    'sys_items',
    'sys_fields',
    'sys_indices',
    'sys_filters',
    'sys_report_params',
    'sys_roles',
    'sys_params',
    'sys_privileges',
    'sys_field_privileges',
    'sys_lookup_lists',
]

def export_task(task, url):
    result = {}
    result['db_type'] = task.task_db_type
    for item_name in metadata_items:
        item = task.item_by_name(item_name)
        copy = item.copy(handlers=False)
        copy.open()
        fields = []
        for field in copy.fields:
            fields.append(field.field_name)
        result[item.item_name] = {'fields': fields, 'records': copy.dataset}
    task_file = 'task.dat'
    file_name = 'task.zip'
    zip_file_name = os.path.join(task.work_dir, file_name)
    try:
        with open(task_file, 'w') as f:
            json.dump(result, f)
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(task_file)
            zip_dir('', zip_file, include_ext=['.html', '.js'], recursive=False)
            zip_dir('js', zip_file)
            zip_dir('css', zip_file)
            zip_dir(os.path.join('static', 'img'), zip_file)
            zip_dir(os.path.join('static', 'js'), zip_file)
            zip_dir(os.path.join('static', 'css'), zip_file)
            zip_dir(os.path.join('static', 'fonts'), zip_file)
            zip_dir(os.path.join('static', 'builder'), zip_file)
            zip_dir('utils', zip_file, exclude_ext=['.pyc'])
            zip_dir('reports', zip_file, exclude_ext=['.xml', '.ods#'], recursive=True)

        items = task.sys_items.copy()
        items.set_where(type_id=consts.TASK_TYPE)
        items.open()
        result_path = os.path.join(task.work_dir, 'static', 'internal')
        if not os.path.exists(result_path):
            os.makedirs(result_path)
        result_file = '%s_%s_%s_%s.zip' % (items.f_item_name.value, consts.VERSION,
            task.app.jam_version, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.rename(to_str(zip_file_name, 'utf-8'), os.path.join(to_str(result_path, 'utf-8'),
            to_str(result_file, 'utf-8')))
        if url:
            result = '%s/static/internal/%s' % (url, result_file)
        else:
            result = result_file
    finally:
        if os.path.exists(task_file):
            os.remove(task_file)
        if os.path.exists(file_name):
            os.remove(file_name)
    return result

def zip_dir(directory, zip_file, exclude_dirs=[], include_ext=None, exclude_ext=[], recursive=True):
    folder = os.path.join(os.getcwd())
    if directory:
        folder = os.path.join(os.getcwd(), directory)
    if os.path.exists(folder):
        if recursive:
            for dirpath, dirnames, filenames in os.walk(folder):
                head, tail = os.path.split(dirpath)
                if not tail in exclude_dirs:
                    for file_name in filenames:
                        name, ext = os.path.splitext(file_name)
                        if (not include_ext or ext in include_ext) and not ext in exclude_ext:
                            file_path = os.path.join(dirpath, file_name)
                            arcname = os.path.relpath(os.path.join(directory, file_path))
                            zip_file.write(file_path, arcname)
        else:
            for file_name in os.listdir(folder):
                name, ext = os.path.splitext(file_name)
                if (not include_ext or ext in include_ext) and not ext in exclude_ext:
                    file_path = os.path.join(folder, file_name)
                    arcname = os.path.relpath(os.path.join(directory, file_path))
                    zip_file.write(file_path, arcname)
