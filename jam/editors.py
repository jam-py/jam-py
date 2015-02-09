# -*- coding:utf-8 -*-

import gtk
import pango
import interface
import gobject
import common
from events import get_events
import client_classes
from third_party.undobuffer import UndoableBuffer, UndoableInsert
from third_party.jsparser import parse, SyntaxError_
from third_party.pyperclip import copy, paste


class EditorBuffer(UndoableBuffer):
    tab = ' ' * common.EDITOR_TAB_SIZE
    def __init__(self, keywords, comment_sign, multiline_signs, multiline_color):
        UndoableBuffer.__init__(self)
        self.modified = False
        self.selected_line = None
        self.keywords = keywords
        self.comment_sign = comment_sign
        self.multiline_signs = multiline_signs
        self.multiline_color = multiline_color
        self.keyword_tag = self.create_tag("keyword", foreground='navy', weight=pango.WEIGHT_BOLD)
        self.comment_tag = self.create_tag("comment", foreground='snow4')
        self.digits_tag = self.create_tag("digits", foreground='sea green')
        self.multiline_tag = self.create_tag("multiline", foreground=self.multiline_color)
        self.text_tag = self.create_tag("text", foreground='orange')
        self.select_line_tag = self.create_tag("select_line", background='lightgray')
        self.bracket_tag = self.create_tag("bracket", foreground='blue', background='alice blue')
        self.multilines = []

    def undo(self):
        if not self.undo_stack:
            return
        self.begin_not_undoable_action()
        self.undo_in_progress = True
        undo_action = self.undo_stack.pop()
        self.redo_stack.append(undo_action)
        if isinstance(undo_action, UndoableInsert):
            start = self.get_iter_at_offset(undo_action.offset)
            stop = self.get_iter_at_offset(
                undo_action.offset + undo_action.length
            )
            self.delete(start, stop)
            self.place_cursor(start)
        else:
            start = self.get_iter_at_offset(undo_action.start)
            stop = self.get_iter_at_offset(undo_action.end)
            start_mark = self.create_mark('start', start, True)
            stop_mark = self.create_mark('stop', stop)
            self.insert(start, undo_action.text)
            if undo_action.delete_key_used:
                start = self.get_iter_at_mark(start_mark)
                self.place_cursor(start)
            else:
                stop = self.get_iter_at_mark(stop_mark)
                self.place_cursor(stop)
            self.delete_mark(start_mark)
            self.delete_mark(stop_mark)
        self.end_not_undoable_action()
        self.undo_in_progress = False

    def clear_undo_stack(self):
        self.undo_stack = []
        self.redo_stack = []

    def select_line(self, line):
        self.unselect_line()
        start = self.get_iter_at_line(line)
        end = self.get_iter_at_line(line + 1)
        self.apply_tag(self.select_line_tag, start, end)
        self.selected_line = line

    def unselect_line(self):
        start = self.get_start_iter()
        end = self.get_end_iter()
        self.remove_tag(self.select_line_tag, start, end)


    def indent_lines(self):

        def indent_line(line_start_iter):
            self.insert(line_start_iter, self.tab)

        self.modify_selection(indent_line)

    def unindent_lines(self):

        def unindent_line(line_start_iter):
            end = line_start_iter.copy()
            end.forward_to_line_end()
            text = line_start_iter.get_text(end)
            if text[:len(self.tab)] == self.tab:
                tab_iter = line_start_iter.copy()
                tab_iter.set_line_offset(len(self.tab))
                self.delete(line_start_iter, tab_iter)

        self.modify_selection(unindent_line)

    def comment_lines(self):

        def comment_line(line_start_iter):
            end = line_start_iter.copy()
            end.forward_to_line_end()
            text = line_start_iter.get_text(end)
            if text.strip()[:len(self.comment_sign)] == self.comment_sign:
                index = text.find(self.comment_sign)
                start = line_start_iter.copy()
                start.set_line_offset(index)
                end = line_start_iter.copy()
                end.set_line_offset(index + len(self.comment_sign))
                self.delete(start, end)
            else:
                self.insert(line_start_iter, self.comment_sign)

        self.modify_selection(comment_line)

    def modify_selection(self, func):
        bounds = self.get_selection_bounds()
        if bounds:
            start, end = bounds
            start_line = start.get_line()
            end_line = end.get_line()
            if end.get_line_offset() == 0:
                end_line -= 1
            for line in range(start_line, end_line + 1):
                line_start = self.get_iter_at_line(line)
                func(line_start)
            start = self.get_iter_at_line(start_line)
            end = self.get_iter_at_line(end_line + 1)
            last = self.get_end_iter()
            if last.get_line() < end_line + 1:
                end = last
            self.expand_range_to_lines(start, end)
            self.select_range(start, end)
            self.apply_syntax(start, end)

    def expand_range_to_lines(self, start, end):
        start.set_line_offset(0)
        if not end.get_line_offset() == 0:
            end.set_line_offset(0)
            if not end.ends_line():
                end.forward_to_line_end()

    def expand_range_to_word(self, start, end):
        repeat = False
        line_start = start.copy()
        line_end = end.copy()
        self.expand_range_to_lines(line_start, line_end)
        text = line_start.get_text(line_end)
        if not start.starts_word() and not start.starts_line():
            start.backward_word_start()
        old_end = end.copy()
        if not end.ends_word() and not end.ends_line():
            end.forward_word_end()
        if old_end.get_line() != end.get_line():
            end.set_line(old_end.get_line())
            end.set_line_offset(old_end.get_line_offset())
        out_text = start.get_text(end)
        pos = start.get_line_offset()
        if pos > 0:
            try:
                if text[pos-1] == '_':
                    start.set_line_offset(pos - 1)
                    repeat = True
            except:
                pass
        if not end.ends_line():
            end_pos = end.get_line_offset()
            if end_pos < len(text) and text[end_pos] == '_':
                if end_pos + 1 < len(text):
                    end.set_line_offset(end.get_line_offset() + 1)
                    if not end.ends_line():
                        repeat = True
        if repeat:
            self.expand_range_to_word(start, end)

    def apply_syntax(self, start=None, end=None):

        def search_text(start, end, delim):

            def search_line_text(start, end, delim):

                def highlight_text(start_index, end_index):
                    t_start = start.copy()
                    t_end = start.copy()
                    t_start.forward_chars(start_index)
                    t_end.forward_chars(end_index + 1)
                    self.apply_tag(self.text_tag, t_start, t_end)

                text = self.get_text(start, end).decode('utf-8')
                first = None
                first_ch = None
                i = 0
                for ch in text:
                    if first is None and ch == delim:
                        first = i
                        first_ch = ch
                    elif not (first is None) and ch == first_ch:
                        highlight_text(first, i)
                        first = None
                        first_ch = None
                    i += 1

            match = start.forward_search(delim, 0, end)
            if match != None:
                match_start, match_end = match
                if not match_end.ends_line():
                    match_end.forward_to_line_end()
                search_line_text(match_start, match_end, delim)
                if match_end.compare(end) == -1:
                    search_text(match_end, end, delim)


        def search_digits(start, end):

            def is_digit(ch):
                return ch.isdigit() or ch == '.'

            def highlight_digits(start_index, end_index):
                d_start = start.copy()
                d_end = start.copy()
                d_start.forward_chars(start_index)
                d_end.forward_chars(end_index)
                self.apply_tag(self.digits_tag, d_start, d_end)

            text = self.get_text(start, end).decode('utf-8')
            prev_ch = ''
            first = None
            i = 0
            for ch in text:
                if ch.isdigit() and prev_ch in ('', ' ', '-', '+', '(', '/', '=', '\t', '\n', '['):
                    first = i
                elif not (first is None) and is_digit(prev_ch) and not is_digit(ch):
                    highlight_digits(first, i)
                    first = None
                prev_ch = ch
                i += 1
            if not first is None:
                highlight_digits(first, i)

        def search_strings(text, start, end):
            pass

        def search_keyword(text, start, end):
            match = start.forward_search(text, 0, end)
            if match != None:
                match_start, match_end = match
                self.expand_range_to_word(match_start, match_end)
                found_text = self.get_text(match_start, match_end)
                if found_text == text:
                    self.apply_tag(self.keyword_tag, match_start, match_end)
                if match_end.compare(end) == -1:
                    search_keyword(text, match_end, end)

        def search_comments(start, end):
            match = start.forward_search(self.comment_sign, 0, end)
            if match != None:
                match_start, match_end = match
                if not match_end.ends_line():
                    match_end.forward_to_line_end()
                self.remove_all_tags(match_start, match_end)
                self.apply_tag(self.comment_tag, match_start, match_end)
                if match_end.compare(end) == -1:
                    search_comments(match_end, end)

        def update_multilines():
            for start_mark, end_mark in self.multilines:
                start =  self.get_iter_at_mark(start_mark)
                end =  self.get_iter_at_mark(end_mark)
                self.remove_all_tags(start, end)
                self.apply_tag(self.multiline_tag, start, end)

        try:
            if not start:
                start = self.get_start_iter()
                end = self.get_end_iter()
            self.remove_all_tags(start, end)
            for key in self.keywords:
                search_keyword(key, start, end)
            search_digits(start, end)
            search_text(start, end, "'")
            search_text(start, end, '"')
            search_comments(start, end)
            update_multilines()
        except:
            pass

    def multiline_change(self):

        def dif_marks(mark1, mark2):
            iter1 = self.get_iter_at_mark(mark1)
            iter2 = self.get_iter_at_mark(mark2)
            return not iter1.equal(iter2)

        def changed(old, new):
            if len(old) != len(new):
                return True
            else:
                for i, j in enumerate(old):
                    if dif_marks(old[i][0], new[i][0]) or dif_marks(old[i][1], new[i][1]):
                        return True

        old = list(self.multilines)
        self.multilines = []
        for (start_sign, end_sign) in self.multiline_signs:
            start = self.get_start_iter()
            end = self.get_end_iter()
            while start != None:
                match = start.forward_search(start_sign, 0, end)
                start = None
                if match != None:
                    match_start, match_end = match
                    match = match_end.forward_search(end_sign, 0, end)
                    match_end = None
                    if match != None:
                        match_end = match[1]
#                        match_end.forward_chars(len(end_sign))
                        start = match_end
                    if match_end is None:
                        match_end = end
                    self.multilines.append((self.create_mark(None, match_start), self.create_mark(None, match_end)))
        result = changed(old, self.multilines)
        for start_mark, end_mark in old:
            self.delete_mark(start_mark)
            self.delete_mark(end_mark)
        return result

search_text = ''

class Editor(object):

    def __init__(self, widget, module_name, item, parent_type_id, module_type, is_report=False):
        self.win = interface.RunTimeDialog(widget, u'Module: ' + module_name,
            width=1280, height=960)

        self.save_button = self.win.add_button(item.task.lang['save'], self.save_and_edit, button_width=100)
        self.cancel_button = self.win.add_button(item.task.lang['cancel'], self.cancel, button_width=100)
        self.win.window.connect('delete-event', self.close)
        self.win.window.connect("key-press-event", self.win_keypressed)
        self.item = item
        self.parent_type_id = parent_type_id
        if module_type == common.SERVER_MODULE:
            self.field = item.f_server_module
        elif module_type == common.CLIENT_MODULE:
            self.field = item.f_client_module
        elif module_type == common.WEB_CLIENT_MODULE:
            self.field = item.f_web_client_module
        if module_type == common.WEB_CLIENT_MODULE:
            self.keywords = ('var', 'function', 'for', 'in', 'is', 'if', 'else',
                'return', 'switch', 'case', 'try', 'catch', 'finally', 'throw', 'while', 'break', 'continue',
                'this', 'true', 'false', 'null', 'undefined', 'delete')
            self.comment_sign = '//'
            self.func_literal = 'function '
            self.multilines = (('/*', '*/'),)
            self.multiline_color = 'snow4'
        else:
            self.keywords = ('def', 'for', 'in', 'is', 'if', 'elif',
                'else', 'return', 'from', 'and', 'not', 'or', 'raise',
                'try', 'except', 'finally', 'import', 'class', 'while', 'break',
                'continue', 'del', 'assert', 'this', 'True', 'False', 'print',
                'None', 'pass')
            self.comment_sign = '#'
            self.func_literal = 'def '
            self.multilines = (('"""', '"""'), ("'''", "'''"))
            self.multiline_color = 'royal blue'
        self.module_type = module_type
        self.is_report = is_report
        self.module_name = module_name
        text = self.read_text()
        self.info = self.item.task.server_get_info(item.id.value)
        global search_text
        self.search_text = search_text
#        self.search_text = ''
        self.replace_text = ''
        self.search_mark = None
        self.replacing = None
        self.treestores = []
        if not text:
            text = ''
        self.events = get_events(self.item.type_id.value, self.module_type == common.SERVER_MODULE)
        self.info[common.editor_tabs[common.TAB_EVENTS]] = self.events
        self.info[common.editor_tabs[common.TAB_FUNCS]] = self.get_funcs_info(text)

        hpaned = gtk.HPaned()

        parents = []

        def tab_clicked(nb, page, page_num):
            self.info_index = page_num

        self.notebook = gtk.Notebook()

        for i, tab in enumerate(common.editor_tabs):
            frame = gtk.Frame('')
            parents.append(frame)
            frame.set_border_width(0)
            label = gtk.Label(tab)
            label.set_markup('<small>%s</small>' % tab);

            sw = gtk.ScrolledWindow()
            sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            treeview = gtk.TreeView()
            tvcolumn = gtk.TreeViewColumn('')
            treeview.append_column(tvcolumn)
            treeview.connect('row-activated', self.tree_dbl_clicked)
            treeview.set_headers_visible(False)
            cell = gtk.CellRendererText()
            font = pango.FontDescription('monospace 9')
            cell.set_property('font-desc', font)
            tvcolumn.pack_start(cell, True)
            tvcolumn.add_attribute(cell, 'text', 0)
            sw.add(treeview)
            treestore = gtk.TreeStore(str)
            self.treestores.append(treestore)
            self.load_info(treestore, self.info[tab])
            treeview.set_model(treestore)
            frame.add(sw)
            self.notebook.append_page(frame, label)

        self.notebook.connect('switch-page', tab_clicked)
        hpaned.add1(self.notebook)

        self.cursor_offset = 0
        self.brackets_processing = False

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textbuffer = EditorBuffer(self.keywords, self.comment_sign, self.multilines, self.multiline_color)
        self.textbuffer.set_text(text.decode('utf-8'))
        #~ self.buffer_changed(self.textbuffer)
        self.textbuffer.multiline_change()
        self.textbuffer.apply_syntax()
        pos = self.textbuffer.get_iter_at_line(0)
        self.textbuffer.place_cursor(pos)
        self.textbuffer.clear_undo_stack()
        self.textbuffer.set_modified(False)
        self.textbuffer.connect("paste-done", self.paste_done)
        self.textbuffer.connect('mark-set', self.cursor_moved)
        self.textbuffer.connect('changed', self.buffer_changed)
        self.textview = gtk.TextView(self.textbuffer)
        self.textview.connect("key-press-event", self.keypressed)
        self.textview.connect("button-press-event", self.button_pressed)
        self.textview.connect("event-after", self.event_after)
        self.textview.connect("populate-popup", self.populate_popup)
        fontdesc = pango.FontDescription("monospace 10")
        self.textview.modify_font(fontdesc)
        sw.add(self.textview)
        hpaned.add2(sw)
        hpaned.set_position(250)

        self.win.body.pack_start(hpaned)
        self.status_label = gtk.Label('')
        self.status_label.set_alignment(0, 0.5)
        self.win.btns_box.pack_start(self.status_label, True)
        self.error_label = gtk.Label('')
        self.error_label.set_alignment(0, 0.5)
        self.win.btns_box.pack_start(self.error_label, True)
        self.error_label.show()
        self.win.show()
        if not self.item.type_id.value in [common.CATALOG_TYPE, common.JOURNAL_TYPE,
            common.TABLE_TYPE, common.DETAIL_TYPE]:
            page = self.notebook.get_nth_page(common.TAB_FIELDS)
            page.hide()
        self.textview.grab_focus()

    def load_info(self, treestore, info, parent_iter=None):

        def fill_treestore(treestore, info, parent_iter=None):
            for key in sorted(info.iterkeys()):
                piter = treestore.append(parent_iter, [key])
                if isinstance(info[key], dict):
                    fill_treestore(treestore, info[key], piter)

        treestore.clear()
        fill_treestore(treestore, info, parent_iter)

    def get_funcs_info(self, text):

        def check_line(line):
            func_name = ''
            trimed_line = line.strip()
            if len(trimed_line) > 0:
                if not (trimed_line[:len(self.comment_sign)] == self.comment_sign):
                    indent = line.find(self.func_literal)
                    if indent >= 0:
                        def_end = line.find('(')
                        if def_end > indent:
                            func_name = line[indent+len(self.func_literal):def_end].strip()
                            return (indent, func_name)

        def add_child_funcs(i, parent_indent, parent_dic, parent_key):
            dic = {}
            parent_dic[parent_key] = dic
            if i < len(funcs_list):
                cur_indent = funcs_list[i][0]
            else:
                return
            cur_indent = -1
            child_indent = -1
            while i < len(funcs_list):
                (indent, func_name) = funcs_list[i]
                if cur_indent == -1:
                    cur_indent = indent
                if indent == cur_indent:
                    dic[func_name] = None
                    cur_func_name = func_name
                elif indent > cur_indent:
                    if child_indent == -1:
                        child_indent = indent
                    if not indent > child_indent:
                        i = add_child_funcs(i, indent, dic, cur_func_name)
                elif indent < cur_indent:
                    return i - 1
                i += 1
            return i

        lines = text.splitlines()
        funcs_list = []
        for i, line in enumerate(lines):
            res = check_line(line)
            if res:
                funcs_list.append(res)
        funcs = {}
        add_child_funcs(0, -1, funcs, 'result')
        return funcs['result']

    def tree_dbl_clicked(self, treeview, path, view_column):
        model = treeview.get_model()
        iter = model.get_iter(path)
        text = model.get_value(iter, 0)
        parent_iter = model.iter_parent(iter)
        if parent_iter:
            parent_text = model.get_value(parent_iter, 0)
        if self.info_index in (common.TAB_EVENTS, common.TAB_FUNCS):
            start = self.textbuffer.get_start_iter()
            found = start.forward_search(self.func_literal + text + '(', 0, None)
            if not found:
                found = start.forward_search(text, 0, None)
            if found:
                self.textbuffer.place_cursor(found[0])
                pos = found[0]
                self.textbuffer.select_line(pos.get_line())
            else:
                if self.info_index == common.TAB_EVENTS:
                    end = self.textbuffer.get_end_iter()
                    line = end.get_line()
                    while line > 0:
                        prev_line = self.textbuffer.get_iter_at_line(end.get_line() - 1)
                        if prev_line.get_text(end).strip() == '':
                            end = prev_line
                            line = end.get_line()
                        else:
                            break
                    params_text = self.events[text]
                    if self.module_type in (common.CLIENT_MODULE, common.SERVER_MODULE):
                        event_text =  '\n\ndef %s(%s):\n%spass' % (text, params_text, self.textbuffer.tab)
                    elif self.module_type ==common.WEB_CLIENT_MODULE:
                        event_text =  '\n\nfunction %s(%s) {\n}' % (text, params_text)
                    start_line = end.get_line()
                    self.textbuffer.insert(end, event_text)
                    start = self.textbuffer.get_iter_at_line(start_line)
                    pos = self.textbuffer.get_end_iter()
                    self.textbuffer.apply_syntax(start, pos)
                    self.textbuffer.place_cursor(pos)
                    self.update_buttons()
            self.scroll_to_line(pos.get_line())
        else:
            self.textbuffer.insert_at_cursor(text)
        gobject.timeout_add(10, lambda: self.textview.grab_focus())

    def scroll_to_line(self, line, select=True):
        pos = self.textbuffer.get_iter_at_line(line)
        pos_mark = self.textbuffer.create_mark('pos_mark', pos)
        self.textview.scroll_mark_onscreen(pos_mark)
        self.textbuffer.delete_mark(pos_mark)
        self.textview.scroll_to_iter(pos, 0, True)
        self.textbuffer.place_cursor(pos)
        if select:
            self.textbuffer.select_line(pos.get_line())
        self.textview.grab_focus()

    def cancel(self, widget):
        self.item.cancel()
        self.win.close()

    def close(self, widget, event=None):
        if self.textbuffer.get_modified():
            res = interface.yes_no_cancel(self.win.window, self.item.task.lang['text_changed'])
            if res == gtk.RESPONSE_YES:
                self.save(widget)
            elif res == gtk.RESPONSE_NO:
                self.item.cancel()
            else:
                return True
        else:
            if self.item:
                self.item.cancel()

    def read_text(self):
        pass

    def save_text(self, text):
        pass

    def update_func_tab(self, text):
        self.load_info(self.treestores[0], self.get_funcs_info(text))

    def check(self, text):
        compile(text, self.module_name, "exec")

    def save_and_edit(self, widget):
        if self.save(widget):
            self.item.edit()

    def save(self, widget):
        error = None
        line = None
        col = None
        result = False
        text = self.textbuffer.get_text(self.textbuffer.get_start_iter(), self.textbuffer.get_end_iter())
        try:
            if self.textbuffer.get_modified():
                self.check(text)
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    lines[i] = line.rstrip()
                text = '\n'.join(lines)
                text = text.rstrip('\n')
                self.save_text(text)
                self.update_func_tab(text)

                self.textbuffer.clear_undo_stack()
                self.textbuffer.set_modified(False)
                self.update_buttons()
                self.show_module_status()
                result = True
        except SyntaxError_, e:
            try:
                err_str = e.args[0]
                pos = err_str.find('\nNone:')
                error = err_str[:pos]
                error = 'invalid systax'
                try:
                    line = int(err_str[pos+len('\nNone:'):])
                except:
                    pass
                if line:
                    error += ' - line %s' % line
            except:
                error = e.message
        except Exception, e:
            try:
                line = e.args[1][1]
                col = e.args[1][2]
                if line and col:
                    error = ' %s - line %d col %d' % (e.args[0], line, col)
                elif line:
                    error = ' %s - line %d col %d' % (e.args[0], line)
                else:
                    error = e.args[0]
            except:
                error = e.message
        if error:
            self.show_status(error, True)
            try:
                if line:
                    self.scroll_to_line(line - 1)
            except:
                pass
            result = False
        return result

    def show_module_status(self):
        self.status_label.set_text('modified: %s line: %d col: %d' % (self.textbuffer.get_modified(), self.cur_pos()[0], self.cur_pos()[1]))

    def update_buttons(self):
        self.save_button.set_sensitive(self.textbuffer.get_modified())
        self.cancel_button.set_sensitive(self.textbuffer.get_modified())

    def event_after(self, widget, event):
        if not event.type in [gtk.gdk.EXPOSE, gtk.gdk.MOTION_NOTIFY, gtk.gdk.FOCUS_CHANGE]:
            self.update_buttons()
            self.show_module_status()

    def populate_popup(self, textview, menu):

        def add_item(caption, handler, active=True):
            menu_item = gtk.MenuItem('')
            label = menu_item.get_children()[0]
            label.set_markup(caption)
            menu.append(menu_item)
            menu_item.set_sensitive(active)
            menu_item.connect("activate", handler)

        for i in menu.get_children():
            menu.remove(i)

        clp_text = paste()
        sel_text = ''
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            sel_text = self.textbuffer.get_text(bounds[0], bounds[1])

        add_item('Copy                              Ctrl+C', self.copy, len(sel_text) > 0)
        add_item('Paste                             Ctrl+V', self.paste, len(clp_text) > 0)
        add_item('Cut                               Ctrl+X', self.cut, len(sel_text) > 0)
        menu.show_all()

    def buffer_changed(self, buffer):
        if self.textbuffer.multiline_change():
            self.textbuffer.apply_syntax()
        else:
            insert_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(insert_mark)
            start.set_line_offset(0)
            end = start.copy()
            end.forward_line()
            self.textbuffer.apply_syntax(start, end)

    def cursor_moved(self, textbuffer, iter, textmark):

        def show_bracket(iter):
            iter_end = iter.copy()
            iter_end.forward_char()
            self.textbuffer.apply_tag(self.textbuffer.bracket_tag, iter, iter_end)

        def hide_bracket(mark_name):
            mark = self.textbuffer.get_mark(mark_name)
            if mark and not mark.get_deleted():
                iter = self.textbuffer.get_iter_at_mark(mark)
                iter_end = iter.copy()
                iter_end.forward_char()
                self.textbuffer.remove_tag(self.textbuffer.bracket_tag, iter, iter_end)
                self.textbuffer.delete_mark(mark)

        def find_next_bracket(iter, char, direction):
            result = None
            count = 0
            if direction == 1:
                if char == '(':
                    find_char = ')'
                elif char == '{':
                    find_char = '}'
                elif char == '[':
                    find_char = ']'
                start = iter.copy()
                start.forward_char()
                end = iter.copy()
                end.forward_to_end()
                text = start.get_text(end)
                text = common.empty_strings(text, self.module_type)
                text = common.remove_comments(text, self.module_type, self.comment_sign)
            else:
                if char == ')':
                    find_char = '('
                elif char == '}':
                    find_char = '{'
                elif char == ']':
                    find_char = '['
                end = iter.copy()
                start = self.textbuffer.get_start_iter()
                text = start.get_text(end)
                text = common.empty_strings(text, self.module_type)
                text = common.remove_comments(text, self.module_type, self.comment_sign)
                text = text[::-1]
            for i, ch in enumerate(text):
                if ch == char:
                    count += 1
                if ch == find_char:
                    if count == 0:
                        result = iter.copy()
                        if direction == 1:
                            result.set_offset(result.get_offset() + i + 1)
                        else:
                            result.set_offset(result.get_offset() - i - 1)
                        break
                    else:
                        count -= 1
            return result

        if self.cursor_offset != iter.get_offset() and not self.brackets_processing:
            self.brackets_processing = True
            try:
                hide_bracket('left_bracket');
                hide_bracket('right_bracket');
                self.cursor_offset = iter.get_offset()
                left = None
                right = None
                next_char = iter.get_char()
                if next_char in ('(', '{', '['):
                    left = iter
                    right = find_next_bracket(iter, next_char, 1)
                elif next_char in (')', '}', ']'):
                    right = iter
                    left = find_next_bracket(iter, next_char, -1)
                elif iter.backward_char():
                    prior_char = iter.get_char()
                    if prior_char in ('(', '{', '['):
                        left = iter
                        right = find_next_bracket(iter, prior_char, 1);
                    elif prior_char in (')', '}', ']'):
                        right = iter
                        left = find_next_bracket(iter, prior_char, -1);
                if left:
                    show_bracket(left);
                    self.textbuffer.create_mark('left_bracket', left.copy());
                if right:
                    show_bracket(right);
                    self.textbuffer.create_mark('right_bracket', right.copy());
            finally:
                self.brackets_processing = False

    def cur_pos(self):
        cursor_mark = self.textbuffer.get_insert()
        iter = self.textbuffer.get_iter_at_mark(cursor_mark)
        return (iter.get_line() + 1, iter.get_line_offset() + 1)

    def paste_done(self, txetbuffer, param):
        self.textbuffer.apply_syntax()

    def iter_at_cursor(self):
        cursor_mark = self.textbuffer.get_insert()
        return self.textbuffer.get_iter_at_mark(cursor_mark)

    def find_word_at_cursor(self):
        start = self.iter_at_cursor()
        end = start.copy()
        self.textbuffer.expand_range_to_word(start, end)
        return start, end

    def button_pressed(self, widget, event):
        self.show_status('')
        self.textbuffer.unselect_line()
        if event.type == gtk.gdk._2BUTTON_PRESS:
            start, end = self.find_word_at_cursor()
            self.textbuffer.select_range(start, end)
            return True

    def win_keypressed(self, widget, event):
        key_name = interface.key_name(event.keyval)
        if key_name in ('s', 'S'):
            if event.state & gtk.gdk.CONTROL_MASK:
                if self.save(widget):
                    self.item.edit()
                return True
        elif key_name in ('e', 'E'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.textbuffer.comment_lines()
                return True
        elif key_name in ('i', 'I'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.textbuffer.indent_lines()
                return True
        elif key_name in ('u', 'U'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.textbuffer.unindent_lines()
                return True
        elif key_name in ('z', 'Z'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.textbuffer.undo()
                self.textbuffer.apply_syntax()
                return True
        elif key_name in ('f', 'F'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.start_search(widget)
                return True
        elif key_name in ('l', 'L'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.find_line(widget)
                return True
        elif key_name in ('h', 'H'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.start_search(widget, True)
                return True
        elif key_name in ('c', 'C'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.copy()
#                self.textbuffer.copy_clipboard(self.textview.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD))
                return True
        elif key_name in ('v', 'V'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.paste()
                #~ self.textbuffer.paste_clipboard(self.textview.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD),
                #~ None, self.textview.get_editable())
                self.textbuffer.apply_syntax()
                return True
        elif key_name in ('x', 'X'):
            if event.state & gtk.gdk.CONTROL_MASK:
                self.cut()
                #~ self.textbuffer.cut_clipboard(self.textview.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD),
                    #~ self.textview.get_editable())
                self.textbuffer.apply_syntax()
                return True

    def copy(self, widget=None):
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            text = self.textbuffer.get_text(bounds[0], bounds[1])
            copy(text)

    def paste(self, widget=None):
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            self.textbuffer.delete(bounds[0], bounds[1])
        self.textbuffer.insert_at_cursor(paste())

    def cut(self, widget=None):
        bounds = self.textbuffer.get_selection_bounds()
        if bounds:
            text = self.textbuffer.get_text(bounds[0], bounds[1])
            copy(text)
            self.textbuffer.delete(bounds[0], bounds[1])

    def keypressed(self, widget, event):
        self.show_status('')
        self.textbuffer.unselect_line()
        #~ if event.keyval == gtk.keysyms.Left:
            #~ if event.state & gtk.gdk.CONTROL_MASK:
                #~ iter = self.iter_at_cursor()
                #~ start, end = self.find_word_at_cursor()
                #~ print iter.get_line_offset(), start.get_line_offset(), end.get_line_offset()
                #~ if not iter.equal(start):
                    #~ self.textbuffer.place_cursor(start)
                    #~ return True
        #~ elif event.keyval == gtk.keysyms.Right:
            #~ if event.state & gtk.gdk.CONTROL_MASK:
                #~ start, end = self.find_word_at_cursor()
                #~ self.textbuffer.place_cursor(end)
                #~ return True
        if event.keyval == gtk.keysyms.Return:
            cursor_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(cursor_mark)
            if start.get_line() < self.textbuffer.get_line_count() - 1:
                end = start.copy()
                self.textbuffer.expand_range_to_lines(start, end)
                text = start.get_text(end)
                spaces = 0
                for char in text:
                    if char == ' ':
                        spaces += 1
                    elif char == '\t':
                        spaces += common.EDITOR_TAB_SIZE
                    else:
                        break
                text = text.strip()
                if text[-1:] == ':':
                    spaces += common.EDITOR_TAB_SIZE
                self.textbuffer.insert_at_cursor('\n' + spaces * ' ')
                return True
        elif event.keyval == gtk.keysyms.BackSpace:
            cursor_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(cursor_mark)
            line_offset = start.get_line_offset()
            end = start.copy()
            end.set_line_offset(0)
            text = start.get_text(end)
            text_len = len(text)
            if text_len and text == text_len * ' ':
                if text_len % len(self.textbuffer.tab) == 0:
                    new_text = (text_len / len(self.textbuffer.tab) - 1) * self.textbuffer.tab
                else:
                    new_text = (text_len / len(self.textbuffer.tab)) * self.textbuffer.tab
                self.textbuffer.delete(start, end)
                self.textbuffer.insert_at_cursor(new_text)
                return True
        elif event.keyval == gtk.keysyms.Tab:
            self.textbuffer.insert_at_cursor(self.textbuffer.tab)
            return True

    def show_status(self, value, highlight=False):
        if highlight:
            self.error_label.set_markup('<span color="firebrick">%s</span>' % value)
        else:
            self.error_label.set_text(value)

    def forward_search(self, start, search_text):

        def is_whole_word(line, pos, search_text):
            if pos > 0:
                ch = line[pos - 1]
                if ch.isalpha() or ch == '_':
                    return False
            if pos + len(search_text) < len(line):
                ch = line[pos + len(search_text)]
                if ch.isalpha() or ch == '_':
                    return False
            return True

        case_sencitive = self.sencitive_check_button.get_active()
        whole_words = self.whole_words_check_button.get_active()

        start_line = start.get_line()
        start_offset = start.get_line_offset()
        end = start.copy()
        end.forward_to_end()
        text = start.get_text(end)
        if not case_sencitive:
            text = text.upper()
            search_text = search_text.upper()
        lines = text.splitlines()
        for i, line in enumerate(lines):
            pos = line.find(search_text)
            if pos > -1:
                if whole_words and not is_whole_word(line, pos, search_text):
                    continue
                end_pos = pos + len(search_text)
                if i == 0:
                    pos += start_offset
                    end_pos += start_offset
                found_start = start.copy()
                found_end = start.copy()
                found_start.set_line(start_line + i)
                found_start.set_line_offset(pos)
                found_end.set_line(start_line + i)
                found_end.set_line_offset(end_pos)
                self.text_found = True
                return (found_start, found_end)

    def find(self):
        if self.search_text:
            if not self.search_mark:
                self.search_mark = self.textbuffer.get_insert()
            start = self.textbuffer.get_iter_at_mark(self.search_mark)
            found = self.forward_search(start, self.search_text)
            if found:
                self.textbuffer.select_range(found[0], found[1])
                if self.search_mark and self.search_mark.get_name() != 'insert':
                    self.textbuffer.delete_mark(self.search_mark)
                start, end = self.textbuffer.get_selection_bounds()
                self.search_mark = self.textbuffer.create_mark('search_mark', end)
                self.textview.scroll_to_iter(end, 0, True)
            else:
                self.textbuffer.place_cursor(start)
                if interface.question(self.search_window, self.item.task.lang['text_not_found']) == gtk.RESPONSE_YES:
                    start = self.textbuffer.get_start_iter()
                    self.textbuffer.place_cursor(start)
                    self.search_mark = self.textbuffer.create_mark('search_mark', start)

    def replace(self):
        bounds = self.textbuffer.get_selection_bounds()
        self.textbuffer.delete(bounds[0], bounds[1])
        self.textbuffer.insert(bounds[1], self.replace_text)
        self.text_found = False

    def search_in_task(self, widget, text):

        def close(widget=None):
            win.window.destroy()

        result = self.item.task.server_find_in_task(self.item.task_id.value, text, self.sencitive_check_button.get_active(),
            self.whole_words_check_button.get_active())
        win = interface.RunTimeDialog(widget, u'', width=800, height=500)
        self.search_window = win.window
        self.close_button = win.add_button(self.item.task.lang['close'], close, button_width = 100)
        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        textview = gtk.TextView()
        textbuffer = textview.get_buffer()
        textbuffer.set_text(result)
        fontdesc = pango.FontDescription("monospace 10")
        textview.modify_font(fontdesc)
        sw.add(textview)
        win.body.pack_start(sw, True, True, 0)
        hseparator = gtk.HSeparator()
        win.body.pack_start(hseparator, False, False)
        win.body.show_all()
        win.show()

    def search(self, widget=None):
        global search_text
        if not self.replacing and self.in_task_check_button.get_active():
            self.search_in_task(widget, self.find_entry.get_text())
            return
        if not self.continue_search:
            self.search_text = self.find_entry.get_text()
            search_text = self.search_text
            if self.search_text:
                self.continue_search = True
                if self.replacing:
                    self.replace_text = self.replace_entry.get_text()
                if self.search_mark:
                    self.textbuffer.delete_mark(self.search_mark)
                    self.search_mark = None
        if self.replacing:
            if self.text_found:
                self.replace()
            else:
                self.find()
        else:
            self.find()

    def start_search(self, widget, replace=False):

        def close(widget=None):
            win.window.destroy()

        def find(widget, event):
            if event.keyval == gtk.keysyms.Return:
                self.search()

        def keypressed(widget, event):
            if event.keyval == gtk.keysyms.Escape:
                close(widget)

        def get_search_text():
            sel = self.textbuffer.get_selection_bounds()
            if sel:
                return self.textbuffer.get_text(sel[0], sel[1])
            else:
                cursor_mark = self.textbuffer.get_insert()
                start = self.textbuffer.get_iter_at_mark(cursor_mark)
                text = start.get_text(start)
                end = start.copy()
                self.textbuffer.expand_range_to_word(start, end)
                result = start.get_text(end)
                for ch in result:
                    if not (ch.isalpha() or ch == '_'):
                        result = ''
                        break
                return result

        self.continue_search = False
        self.text_found = False
        self.replacing = replace
        new_text = get_search_text()
        if new_text:
            self.search_text = new_text
            global search_text
            search_text = self.search_text
        win = interface.RunTimeDialog(widget, self.item.task.lang['find'], width=500, height=100, pos_center=False)
        self.search_window = win.window
        win.window.connect("key-press-event", keypressed)
        self.find_button = win.add_button(self.item.task.lang['find'], self.search, button_width = 100)
        self.close_button = win.add_button(self.item.task.lang['cancel'], close, button_width = 100)
        if replace:
            table = gtk.Table(4, 2, False)
        else:
            table = gtk.Table(4, 2, False)
        win.body.pack_start(table, True, True, 0)
        label = gtk.Label(self.item.task.lang['find'] + ' ')
        label.set_property('xalign', 1)
        self.find_entry = gtk.Entry()
        self.find_entry.set_property('xalign', 0)
        self.find_entry.set_text(self.search_text)
        self.find_entry.connect("key-press-event", find)
        table.attach(label, 0, 1, 0, 1, xoptions = gtk.SHRINK, xpadding = 6, ypadding = 6)
        table.attach(self.find_entry, 1, 2, 0, 1, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6, ypadding = 6)
        opt_line = 1
        if replace:
            label = gtk.Label(self.item.task.lang['replace'] + ' ')
            label.set_property('xalign', 0)
            self.replace_entry = gtk.Entry()
            self.replace_entry.set_property('xalign', 0)
            self.replace_entry.set_text(self.replace_text)
            self.replace_entry.connect("key-press-event", find)
            table.attach(label, 0, 1, 1, 2, xoptions = gtk.SHRINK, xpadding = 6)
            table.attach(self.replace_entry, 1, 2, 1, 2, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6)
            opt_line = 2
        self.sencitive_check_button =  gtk.CheckButton(self.item.task.lang['case_sensitive'])
        self.whole_words_check_button =  gtk.CheckButton(self.item.task.lang['whole_words'])
        table.attach(self.sencitive_check_button, 1, 2, opt_line, opt_line + 1, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6)
        table.attach(self.whole_words_check_button, 1, 2, opt_line + 1, opt_line + 2, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6)
        if not replace:
            self.in_task_check_button =  gtk.CheckButton(self.item.task.lang['in_task'])
            table.attach(self.in_task_check_button, 1, 2, opt_line + 2, opt_line + 3, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6)
        hseparator = gtk.HSeparator()
        win.body.pack_start(hseparator, False, False)
        win.body.show_all()
        win.show()
        pos = self.win.window.get_position()
        size = self.win.window.get_size()
        screen_width = gtk.gdk.screen_width()
        left = pos[0] + size[0]
        if left + win.window.get_size()[0] > screen_width:
            left = screen_width - win.window.get_size()[0]
        win.window.move(left, pos[1])

    def find_line(self, widget):

        def close(widget=None):
            win.window.destroy()

        def find(widget, event):
            if event.keyval == gtk.keysyms.Return:
                text = self.find_line_entry.get_text()
                try:
                    line = int(text)
                except:
                    line = 0
                if line:
                    self.scroll_to_line(line - 1)
                    close()

        def keypressed(widget, event):
            if event.keyval == gtk.keysyms.Escape:
                close(widget)

        win = interface.RunTimeDialog(widget, self.item.task.lang['go_to_line'], width=200, height=100)
        win.window.connect("key-press-event", keypressed)
        self.find_button = win.add_button(self.item.task.lang['go_to'], self.search, button_width = 100)
        self.close_button = win.add_button(self.item.task.lang['cancel'], close, button_width = 100)
        table = gtk.Table(1, 2, False)
        win.body.pack_start(table, True, True, 0)
        label = gtk.Label(self.item.task.lang['line'])
        label.set_property('xalign', 0)
        self.find_line_entry = gtk.Entry()
        self.find_line_entry.set_property('xalign', 1)
        self.find_line_entry.connect("key-press-event", find)
        table.attach(label, 0, 1, 0, 1, xoptions = gtk.SHRINK, xpadding = 6, ypadding = 6)
        table.attach(self.find_line_entry, 1, 2, 0, 1, xoptions=gtk.EXPAND|gtk.FILL, xpadding = 6, ypadding = 6)
        hseparator = gtk.HSeparator()
        win.body.pack_start(hseparator, False, False)
        win.body.show_all()
        win.show()

class FieldEditor(object):
    def __init__(self, item, widget, title, source_def, source_list,
        dest_def, dest_list, save_action, cancel_action=None, can_move=True, read_only=False):
        self.item = item
        self.source_def = source_def
        self.source_list = source_list
        self.dest_def = dest_def
        self.dest_list = dest_list
        self.save_action = save_action
        self.cancel_action = cancel_action
        self.prune_source()
        dic = {
            "save_button_clicked": self.save_btn_clicked,
            "cancel_button_clicked": self.cancel_btn_clicked,
            "left_button_clicked": self.left_btn_clicked,
            "right_button_clicked": self.right_btn_clicked,
            "up_button_clicked": self.up_btn_clicked,
            "down_button_clicked": self.down_btn_clicked,
            }
        self.builder = gtk.Builder()
        self.builder.add_from_string(item.task.get_ui_file('adm_fields_editor.ui'))
        self.builder.connect_signals(dic)
        if not can_move or read_only:
            self.builder.get_object('down_button').hide()
            self.builder.get_object('up_button').hide()
        if read_only:
            self.builder.get_object('left_button').hide()
            self.builder.get_object('right_button').hide()
        self.window = self.builder.get_object('window1')
        self.window.connect("delete-event", self.do_delete)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_title(title)
        self.window.set_transient_for(interface.get_widget_window(widget))
        self.window.set_modal(True)
        self.window.set_default_size(650, 400)

        self.left_box = self.builder.get_object('left_vbox')
        self.left_grid = interface.ListGrid(dest_def, dest_list)
#        self.left_grid.refresh()
        self.left_box.add(self.left_grid)
        self.left_box.show_all()

        self.right_box = self.builder.get_object('right_vbox')
        self.right_grid = interface.ListGrid(source_def, source_list)
#        self.right_grid.refresh()
        self.right_box.add(self.right_grid)
        self.right_box.show_all()
        self.modified = False

    def show(self):
        self.window.show()

    def prune_source(self):
        for dest_item in list(self.dest_list):
            found = False
            for i, source_item in enumerate(self.source_list):
                if source_item[0] == dest_item[0]:
                    dest_item.insert(1, source_item[1])
                    self.source_list.pop(i)
                    found = True
                    break
            if not found:
                self.dest_list.remove(dest_item)


    def left_btn_clicked(self, widget):
        iter = self.right_grid.get_row_iter()
        self.left_grid.add_row(self.right_grid.store, iter)
        self.right_grid.remove_row(iter)
        self.modified = True

    def right_btn_clicked(self, widget):
        iter = self.left_grid.get_row_iter()
        self.right_grid.add_row(self.left_grid.store, iter)
        self.left_grid.remove_row(iter)
        self.modified = True

    def up_btn_clicked(self, widget):
        iter = self.left_grid.get_row_iter()
        if iter:
            self.left_grid.swap_row(iter, -1)
        self.modified = True

    def down_btn_clicked(self, widget):
        iter = self.left_grid.get_row_iter()
        if iter:
            self.left_grid.swap_row(iter, 1)
        self.modified = True

    def save_btn_clicked(self, widget):
        try:
            result = []
            for row in self.left_grid.store:
                row_list = []
                for i in range(self.left_grid.store.get_n_columns()):
                    if i != 1:
                        row_list.append(row[i])
                result.append(row_list)
            if self.save_action:
                self.save_action(result)
            self.window.destroy()
            return True
        except Exception, e:
            print e

    def close(self, widget=None):
        if self.cancel_action:
            self.cancel_action()
        self.window.destroy()

    def cancel_btn_clicked(self, widget):
        self.close(widget)

    def do_delete(self, widget, event):
        if self.modified:
            res = interface.yes_no_cancel(widget, self.item.task.lang['save_changes'])
            if res == gtk.RESPONSE_YES:
                if not self.save_btn_clicked(None):
                    return True
            elif res == gtk.RESPONSE_NO:
                self.cancel_btn_clicked(None)
            else:
                return True
        else:
            if self.cancel_action:
                self.cancel_action()

class ItemEditor(Editor):
    def __init__(self, widget, item, module_name, parent_type_id, module_type):
        Editor.__init__(self, widget, module_name, item, parent_type_id, module_type)

    def read_text(self):
        return self.field.value

    def save_text(self, text):
        self.field.value = unicode(text)
        self.item.post()
        self.item.apply()

class ReportEditor(Editor):
    def __init__(self, widget, item, parent_type_id, module_name):
        Editor.__init__(self, widget, module_name, item, parent_type_id, module_type=common.SERVER_MODULE, is_report=True)

    def read_text(self):
        return self.item.task.server_load_report_module(self.module_name)

    def save_text(self, text):
        self.item.task.server_store_report_module(text, self.module_name)

class JavascriptEditor(Editor):
    def __init__(self, widget, item, parent_type_id, module_name):
        Editor.__init__(self, widget, module_name, item, parent_type_id, module_type=common.WEB_CLIENT_MODULE)

    def check(self, text):
        text = text.replace('.delete(', '["delete"](')
        parse(text)

    def read_text(self):
        return self.field.value

    def save_text(self, text):
        self.field.value = unicode(text)
        self.item.post()
        self.item.apply()
        self.item.task.server_update_events_code(self.item.task_id.value)



