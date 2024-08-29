import os
import sys
import datetime
import zipfile
from xml.dom.minidom import parseString
from xml.sax.saxutils import escape
from subprocess import Popen, STDOUT, PIPE
import uuid
if os.name == "nt":
    try:
        from winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE
    except:
        from _winreg import OpenKey, QueryValue, HKEY_LOCAL_MACHINE

from .common import to_bytes

def tobytes(x):
    return to_bytes(x, 'utf-8')

class Var(object):
    def __init__(self, literal):
        self.literal = tobytes(literal)
        self.var = tobytes(literal[2:-2])

class Cell(object):
    def __init__(self, col, default_formating):
        self.vars = []
        self.col = col
        self.default_formating = default_formating
        self.image = None

class Col(object):
    def __init__(self, repeated):
        if not repeated:
            repeated = 1
        self.repeated = int(repeated)
        self.text = ''

class Row(object):
    def __init__(self, repeated):
        if not repeated:
            repeated = 1
        self.repeated = int(repeated)
        self.cells = []

class Band(object):
    def __init__(self, report, tag=None):
        self.report = report
        self.tag = tag
        self.rows = []
        self.cols = []
        self.text = ''

class Report(object):

    TABLE_END = tobytes('</table:table>')
    START_ROW = tobytes('<table:table-row')
    END_ROW = tobytes('</table:table-row>')
    START_COLUMN = tobytes('<table:table-column')
    END_COLUMN = tobytes('/>')
    START_TEXT = tobytes('<text:p>')
    END_TEXT = tobytes('</text:p>')
    START_PARAM = tobytes('%(')
    END_PARAM = tobytes(')s')

    def prepare_report(self, on_generate, ext='.ods', hidden_columns=None):
        self.hidden_columns = hidden_columns
        self.ext = ext
        file_name = self.gen_file_name()
        self.report_filename = os.path.join(self.dest_folder, file_name)
        self.report_url = os.path.join(self.dest_url, file_name)

        self.header = Band(self)
        self.columns = Band(self)
        self.bands = []
        self.footer = Band(self)
        self.parse()

        self.images = []
        self.cur_row = 1
        self.content_xml = tobytes('')
        self.generate_report(on_generate)
        self.content_xml = None

    def generate_report(self, on_generate):
        if self.on_before_generate:
            self.on_before_generate(self)
        if self.on_parsed:
            self.on_parsed(self)
        self.content_xml += self.header.text
        for col in self.columns.cols:
            self.content_xml += col.text
        if on_generate:
            on_generate(self)
        self.content_xml += self.footer.text
        self.save()
        if self.ext != '.ods':
            self.convert_report()
        if self.on_after_generate:
            self.on_after_generate(self)

    def save(self):
        image_links = self.get_image_links()
        with zipfile.ZipFile(self.report_filename, 'w', zipfile.ZIP_DEFLATED) as dest:
            with zipfile.ZipFile(self.template_path, 'r') as source:
                manifest_data = None
                for file_name in source.namelist():
                    data = source.read(file_name)
                    if file_name == 'content.xml':
                        dest.writestr(file_name, self.content_xml)
                    elif file_name == 'META-INF/manifest.xml':
                        manifest_data = data
                    elif image_links.get(file_name):
                        pass
                    else:
                        dest.writestr(file_name, data)
                if self.images:
                    for new_link, image, link in self.images:
                        dest.write(image, new_link, compress_type = zipfile.ZIP_DEFLATED)
                    manifest_data = self.change_manifest(manifest_data, image_links)
                if manifest_data:
                    dest.writestr('META-INF/manifest.xml', manifest_data)

    def get_image_links(self):
        result = {}
        for new_link, image, link in self.images:
            l = result.get(link)
            if l is None:
                result[link] = []
                l = result[link]
            l.append(new_link)
        return result

    def change_manifest(self, manifest_data, image_links):
        for old_link, new_links in image_links.items():
            old_link = tobytes(old_link)
            pos = manifest_data.find(old_link)
            if pos != -1:
                pos = manifest_data.rfind(tobytes('<manifest:file-entry'), 0, pos)
                pos1 = manifest_data.find(tobytes('/>'), pos)
                old_line = manifest_data[pos:pos1+2]
                new_lines = tobytes('')
                for link in new_links:
                    link = tobytes(link)
                    new_lines += old_line.replace(old_link, link, 1)
                manifest_data = manifest_data.replace(old_line, new_lines, 1)
        return manifest_data

    def convert_report(self):
        converted = False
        if self.on_convert:
            converted = self.on_convert(self)
        else:
            converted = self.convert()
        if converted:
            converted_file_name = self.report_filename.replace('.ods', self.ext)
            if os.path.exists(converted_file_name):
                os.remove(self.report_filename)
                self.report_filename = converted_file_name
                self.report_url = self.report_url.replace('.ods', self.ext)

    def convert(self):
        with self.task.lock('$report_conversion'):
            try:
                from subprocess import Popen, STDOUT, PIPE
                if os.name == "nt":
                    regpath = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\soffice.exe"
                    root = OpenKey(HKEY_LOCAL_MACHINE, regpath)
                    s_office = QueryValue(root, "")
                else:
                    s_office = "soffice"
                convertion = Popen([s_office, '--headless', '--convert-to', self.ext.strip('.'),
                    self.report_filename, '--outdir', self.dest_folder],
                    stderr=STDOUT,stdout=PIPE)
                out, err = convertion.communicate()
            except Exception as e:
                print('Report "%s" conversion error:' % self.name, e)
                return False
            return True

    def gen_file_name(self):
        file_name = escape(self.name, { char: '' for char in ['\\', '/', ':', '*', '"', '<', '>', '|', 'NUL']})
        file_name = file_name + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f') + '.ods'
        return file_name

    def parse(self):
        with zipfile.ZipFile(self.template_path, 'r') as z:
            content = z.read('content.xml')
        dom = parseString(content)
        tables = dom.getElementsByTagName('table:table')
        table = tables[0]
        cur_band = self.header
        self.cur_rows = []
        for child in table.childNodes:
            if child.nodeName == 'table:table-column':
                repeated = child.getAttribute('table:number-columns-repeated')
                self.columns.cols.append(Col(repeated))
            elif child.nodeName == 'table:table-row':
                for row_child in child.childNodes:
                    if row_child.nodeName == 'table:table-cell':
                        text = row_child.getElementsByTagName('text:p')
                        if text.length > 0:
                            tag = text[0].childNodes[0].nodeValue
                            cur_band.rows = self.cur_rows[:]
                            self.cur_rows = []
                            cur_band = Band(self, tag)
                            self.bands.append(cur_band)
                        break
            self.process_rows(child)
        cur_band.rows = self.cur_rows[:]
        if not len(self.bands):
            raise Exception('No bands in the report template "%s"' % self.template_path)
        self.process_bands(content)
        self.bands_dict = { band.tag: band for band in self.bands }

    def process_bands(self, content):
        start = content.find(self.START_COLUMN)
        self.header.text = content[:start]
        for col in self.columns.cols:
            start = content.find(self.START_COLUMN, start)
            end = content.find(self.END_COLUMN, start) + len(self.END_COLUMN)
            col.text = content[start:end]
            start = end
        band_positions = []
        for band in self.bands:
            tag = self.START_TEXT + tobytes(band.tag) + self.END_TEXT
            tag_start = content.find(tag, start)
            start = content.rfind(self.START_ROW, start, tag_start)
            band_positions.append(start)
        end = None
        for row in band.rows:
            if row.repeated > 1000:
                tag = tobytes('table:number-rows-repeated="%s"' % row.repeated)
                tag_start = content.find(tag, start)
                end = content.rfind(self.START_ROW, start, tag_start)
        if not end:
            tag_start = content.find(self.TABLE_END, start)
            end = content.rfind(self.END_ROW, start, tag_start)
            end += len(self.END_ROW)
        band_positions.append(end)
        for i, band in enumerate(self.bands):
            band.text = content[band_positions[i]:band_positions[i+1]]
            band.text = band.text.replace(self.START_TEXT + tobytes(band.tag) + self.END_TEXT, tobytes(''), 1)
        self.footer.text = content[end:]

    def find_vars(self, text):
        result = []
        while True:
            p1 = text.find('%(')
            if p1 != -1:
                p2 = text.find(')s', p1)
                if p2 != -1:
                    result.append(Var(text[p1:p2+2]))
                text = text[p1+2:]
            else:
                break
        return result

    def process_rows(self, node):
        if node.nodeName == 'table:table-row':
            repeated = node.getAttribute('table:number-rows-repeated')
            row = Row(repeated)
            col_count = 1
            for child in node.childNodes:
                if child.nodeName == 'table:table-cell':
                    text = child.getElementsByTagName('text:p')
                    cell = None
                    for t in text:
                        for child_node in t.childNodes:
                            cell_text = child_node.nodeValue
                            if cell_text:
                                trimed = cell_text.strip()
                                cell_vars = self.find_vars(trimed)
                                if cell_vars:
                                    default = t == text[0] and child_node == t.childNodes[0]
                                    if not cell:
                                        cell = Cell(col_count, default)
                                        row.cells.append(cell)
                                    for v in cell_vars:
                                        cell.vars.append(v)
                    draw_frame = child.getElementsByTagName('draw:frame')
                    if draw_frame.length and cell:
                        draw_image = child.getElementsByTagName('draw:image')
                        if draw_image.length:
                            cell.image = {
                                'table:end-cell-address': draw_frame[0].attributes['table:end-cell-address'].value,
                                'xlink:href': draw_image[0].attributes['xlink:href'].value
                            }
                    col_count += 1
                elif child.nodeName == 'table:covered-table-cell':
                    cols = child.getAttribute('table:number-columns-repeated')
                    if cols:
                        col_count += int(cols)
            self.cur_rows.append(row)
        else:
            for child in node.childNodes:
                self.process_rows(child)

    def print_band(self, band_tag, var_dict=None):
        band = self.bands_dict[band_tag]
        cell_vars = {}
        if var_dict:
            for key, value in var_dict.items():
                cell_vars[tobytes(key)] = value
        band_text = band.text
        for row in band.rows:
            for cell in row.cells:
                image_processed = False
                for var in cell.vars:
                    value = cell_vars.get(var.var)
                    image = None
                    if not value is None:
                        if isinstance(value, str):
                            text = tobytes(escape(value).replace('\n', '</text:p><text:p>'))
                        elif isinstance(value, int) or type(value) == float:
                            text = tobytes(str(value))
                        elif type(value) == dict and cell.image:
                            image = value.get('image')
                            text = value.get('text', '')
                        else:
                            raise Exception('Invalid cell value type')
                        band_text = band_text.replace(var.literal, tobytes(text), 1)
                        if image:
                            image_processed = True
                            if os.path.exists(image):
                                addres = cell.image['table:end-cell-address']
                                new_addres = '%s.%s%s' % (addres.split('.')[0], self.col_int_to_str(cell.col), self.cur_row)
                                band_text = band_text.replace(tobytes(addres), tobytes(new_addres), 1)
                                link = cell.image['xlink:href']
                                new_link = 'Pictures/%s%s' % (self.cur_row, self.gen_image_name(image))
                                band_text = band_text.replace(tobytes(link), tobytes(new_link), 1)
                                self.images.append([new_link, image, link])
                            else:
                                link = cell.image['xlink:href']
                                band_text = band_text.replace(tobytes(link), tobytes(''), 1)
                if cell.image and not image_processed:
                    link = cell.image['xlink:href']
                    band_text = band_text.replace(tobytes(link), tobytes(''), 1)
            self.cur_row += row.repeated
        self.content_xml += band_text

    def gen_image_name(self, image_path):
        return uuid.uuid4().hex + os.path.splitext(image_path)[1]

    def hide_columns(self, hidden_columns):
        if hidden_columns:
            cols = []
            for col in self.columns.cols:
                if col.repeated > 1:
                    parts = col.text.split(tobytes(' '))
                    text = tobytes(' ').join([ part for part in parts if part.find(tobytes('table:number-columns-repeated')) == -1])
                    for i in range(col.repeated):
                        new_col = Col(1)
                        new_col.text = text
                        cols.append(new_col)
                else:
                    cols.append(col)
            hidden_ints = [ self.col_str_to_int(c) for c in hidden_columns ]
            for i, col in enumerate(cols):
                if i + 1 in hidden_ints:
                    col.text = col.text[0:-2] + tobytes(' table:visibility="collapse"/>')
            self.columns.cols = []
            for col in cols:
                self.columns.cols.append(col)

    def col_str_to_int(self, s):
        if type(s) == int:
            return s
        s = s.upper()
        base = ord('A')
        mult = ord('Z') - base + 1
        result = 0
        chars = [ s[i] for i in range(len(s))]
        for i, char in enumerate(reversed(chars)):
            result += (ord(chars[i]) - base + 1) * (mult ** (len(chars) - i - 1))
        return result

    def col_int_to_str(self, i):
        base = ord('A')
        mult = ord('Z') - base + 1
        result = ''
        d = i
        while True:
            d -= 1
            d, m = divmod(d, mult)
            c = chr(m + base)
            result = c + result
            if d == 0:
                break
        return result
