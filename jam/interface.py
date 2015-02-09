# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
except:
    print("GTK Not Availible")
    sys.exit(1)
import pango
import glib

from xml.sax.saxutils import escape
import logging
import traceback

import third_party.CairoPlot
import common
from lang.langs import LANGUAGE
import datetime

class FieldInterface(object):
    def __init__(self):
        self.controls = []
        self.on_entry_button_click = None
        self.on_entry_drop_down_click = None
        self.on_entry_clear_click = None

    def show_error_mark(self, value):
        for contr in self.controls:
            if isinstance(contr, DBEntry):
                label = contr.label
                if label:
                    label_name = self.field_caption
                    if self.filter:
                        label_name = self.filter.filter_caption
                    if value:
                        label.set_markup('<span color="firebrick">%s</span>' % label_name)
                    else:
                        label.set_markup('%s' % label_name)

    def create_entry(self, i, table, col_count=1, label_on_top=False, label_name=None, sel_from_view_form=True,
            sel_from_dropdown_box=False):
        entry = DBEntry(self, sel_from_view_form=sel_from_view_form, sel_from_dropdown_box=sel_from_dropdown_box)
        if not label_name:
            label_name = self.field_caption
        label = gtk.Label(label_name)
        entry.label = label
        if label_on_top:
            label.set_property('xalign', 0)
        else:
            label.set_property('xalign', 1)

        if label_on_top:
            left = i % col_count
            top = i / col_count * 2
            table.attach(label, left, left + 1, top, top + 1, yoptions = gtk.FILL, xpadding = 0)
            table.attach(entry, left, left + 1, top+1, top + 2, yoptions = gtk.FILL|gtk.SHRINK)
        else:
            left = i % col_count * 2
            top = i / col_count
            table.attach(label, left, left + 1, top, top + 1, xpadding = 6)
            table.attach(entry, left + 1, left + 2, top, top + 1, yoptions = gtk.FILL|gtk.SHRINK)

    def select_from_dropdown_box(self, widget, search=None):
        self.show_invalid_mess('')
        RefPopup(self, widget, True, search=search)

    def select_from_view_form(self, widget = None):
        self.show_invalid_mess('')
        copy = self.lookup_item.copy()
        copy.is_lookup_item = True
        if self.filter and self.filter.filter_type == common.FILTER_IN and self.filter.field.lookup_item:
            copy.lookup_selected_ids = {};
            if self.filter.value:
                for val in self.filter.value:
                    copy.lookup_selected_ids[val] = True
        copy.details_active = False
        copy.lookup_field = self
        if self.owner and self.owner.on_param_lookup_item_show:
            self.owner.on_param_lookup_item_show(self, copy)
        if self.owner and self.owner.on_field_lookup_item_show:
            self.owner.on_field_lookup_item_show(self, copy)
        if self.filter and self.filter.owner.on_filter_lookup_item_show:
            self.filter.owner.on_filter_lookup_item_show(self.filter, copy);
        copy.view(widget)

    def show_calender(self, widget = None):
        self.calendar = Calendar(self, widget)

class TaskInterface(object):

    def get_window(self):
        if self.main_form:
            if self.main_form.window:
                result = self.task.main_form.window
        return result

    def question(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        result = question(win, message)
        if result == gtk.RESPONSE_YES:
            return True

    def warning(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        return warning(win, message)

    def error(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        return error(win, message)

    def yes_no_cancel(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        result = yes_no_cancel(win, message)
        if result == gtk.RESPONSE_YES:
            return 1
        elif result == gtk.RESPONSE_NO:
            return 0
        elif result == gtk.RESPONSE_CANCEL:
            return -1
        return result

class ItemInterface(object):
    def __init__(self):
        self.view_form = None
        self.edit_form = None
        self.filter_form = None
        self.lookup_field = None
        self.is_lookup_item = False
        self.lookup_selected_ids = None
        self.error_label = None
        self.on_before_show_edit_form = None
        self.on_before_show_view_form = None
        self.on_before_show_filter_form = None
        self.on_edit_keypressed = None
        self.on_view_keypressed = None
        self.on_after_show_edit_form = None
        self.on_after_show_view_form = None
        self.on_after_show_filter_form = None
        self.on_edit_form_close_query = None
        self.on_view_form_close_query = None
        self.on_field_lookup_item_show = None
        self.on_filter_lookup_item_show = None
        self.on_destroy_view_form = None
        self.on_destroy_edit_form = None
        self.on_param_lookup_item_show = None
        self.active_detail = None
        self.list_store = None

    def __getattr__(self, name):
        if name == 'view_ui' :
            obj = self.send_request('get_view_ui')
            if obj:
                setattr(self, name, obj)
                return obj
        elif name == 'edit_ui' :
            obj = self.send_request('get_edit_ui')
            if obj:
                setattr(self, name, obj)
                return obj
        elif name == 'filter_ui' :
            obj = self.send_request('get_filter_ui')
            if obj:
                setattr(self, name, obj)
                return obj
        else:
            raise AttributeError (self.item_name + ' AttributeError: ' + name)

    def show_invalid_mess(self, mess):
        if type(mess) == tuple:
            mess = mess[0]
        if self.edit_form:
            if self.error_label:
                try:
                    self.error_label.set_markup('<span color="firebrick">%s</span>' % mess)
                except:
                    if mess:
                        self.warning(mess)
            elif mess:
                self.warning(mess)
        else:
            if mess:
                print mess

    def create_view_form(self, widget):
        return ItemWindow(self, self.view_ui, widget)

    def view(self, widget):
        self.view_form = self.create_view_form(widget)
        if self.task.on_before_show_view_form:
            self.task.on_before_show_view_form(self)
        if self.owner.on_before_show_view_form:
            self.owner.on_before_show_view_form(self)
        if self.on_before_show_view_form:
            self.on_before_show_view_form(self)
        if self.view_form and self.view_form.window:
            self.view_form.window.connect("key-press-event", self.view_keypressed)
            self.view_form.window.connect('delete-event', self.check_view)
        self.view_form.show()
        if self.task.on_after_show_view_form:
            self.task.on_after_show_view_form(self)
        if self.owner.on_after_show_view_form:
            self.owner.on_after_show_view_form(self)
        if self.on_after_show_view_form:
            self.on_after_show_view_form(self)
        if self.view_form.window:
            self.view_form.window.connect("destroy", self.do_on_destroy_view_form)
        return self.view_form

    def do_on_destroy_view_form(self, window):
        if self.on_destroy_view_form:
            self.on_destroy_view_form(self)

    def view_keypressed(self, widget, event):
        if self.task.on_view_keypressed:
            self.task.on_view_keypressed(self, event)
        if self.owner.on_view_keypressed:
            self.owner.on_view_keypressed(self, event)
        if self.on_view_keypressed:
            self.on_view_keypressed(self, event)
        #~ elif event.keyval == gtk.keysyms.Insert:
            #~ self.insert_record(widget)
        #~ elif event.keyval == gtk.keysyms.Delete:
            #~ if event.state & gtk.gdk.CONTROL_MASK:
                #~ self.delete_record(widget)

    def check_view(self, widget = None, event = None):
        if self.view_form and self.view_form.window:
            can_close = None
            if self.on_view_form_close_query:
                can_close = self.on_view_form_close_query(self)
            if can_close is None and self.owner.on_view_form_close_query and not self.master:
                can_close = self.owner.on_view_form_close_query(self)
            if can_close is None and self.task.on_view_form_close_query:
                can_close = self.task.on_view_form_close_query(self)
            if can_close == False:
                return True
            self.view_form = None

    def close_edit_form(self):
        if self.edit_form.window:
            self.edit_form.window.destroy()
            self.edit_form = None

    def close_filter_form(self):
        if self.filter_form:
            self.filter_form.window.destroy()
            self.filter_form = None

    def set_lookup_field_value(self, widget):
        window = get_widget_window(widget)
        if window:
            window.destroy()
        lookup_field = self.lookup_field
        slave_field_values = {}
        lookup_value = None
        object_field = self.field_by_name(lookup_field.lookup_field)

        if not self.lookup_selected_ids is None:
            ids = []
            lookup_field.value = None
            for key in self.lookup_selected_ids.iterkeys():
                ids.append(key)
            if len(ids):
                lookup_field.filter.value = ids
            elif isinstance(widget, gtk.TreeView):
                lookup_field.filter.value = [self.id.value]
            else:
                lookup_field.filter.value = None
        else:
            if object_field:
                lookup_value = object_field.value
            if lookup_field.owner and lookup_field.owner.fields:
                for field in lookup_field.owner.fields:
                    if field.master_field == lookup_field:
                        object_field = self.field_by_name(field.lookup_field)
                        if object_field:
                            slave_field_values[field.field_name] = object_field.get_value();
            lookup_field.set_value(self.id.value, lookup_value, slave_field_values, self)

    def check_edit(self, widget, event=None):
        can_close = None
        if self.on_edit_form_close_query:
            can_close = self.on_edit_form_close_query(self)
        if can_close is None and self.owner.on_edit_form_close_query and not self.master:
            can_close = self.owner.on_edit_form_close_query(self)
        if can_close is None and self.task.on_edit_form_close_query:
            can_close = self.task.on_edit_form_close_query(self)
        if can_close == False:
            return True
        self.edit_form = None

    def create_grid(self, container, fields=None, dblclick_edit=True, headers=True, lines=False,
        border_width=6, striped=True, multi_select=False,
        multi_select_get_selected=None, multi_select_set_selected=None):
        grid = DBGrid(self, fields, dblclick_edit, headers, lines,
            border_width, striped, multi_select,
            multi_select_get_selected, multi_select_set_selected)
        container.add(grid)
        return grid

    def create_table_grids(self):
        pass

    def set_edit_fields(self, fields):
        for field in self.fields:
            field.edit_visible = False
            field.edit_index = -1
        for i, field_name in enumerate(fields):
            field = self.field_by_name(field_name)
            if field:
                field.edit_visible = True
                field.edit_index = i + 1
            else:
                raise Exception, '%s set_edit_fields: no field for field_name %s' % (self.item_name, field_name)

    def set_view_fields(self, fields):
        for field in self.fields:
            field.view_visible = False
            field.view_index = -1
        for i, field_name in enumerate(fields):
            field = self.field_by_name(field_name)
            if field:
                field.view_visible = True
                field.view_index = i + 1
            else:
                raise Exception, '%s set_view_fields: no field for field_name %s' % (self.item_name, field_name)


    def create_entries(self, container, fields=None, col_count=1, label_on_top=False, sel_from_view_form=True,
            sel_from_dropdown_box=False, row_spacings=6, col_spacings=6, homogeneous=True):
        children = container.get_children()
        for child in list(children):
            container.remove(child)
            child.destroy()
        if fields:
            field_list = []
            for field_name in fields:
                if field_name:
                    try:
                        field = self.field_by_name(field_name)
                        field_list.append(field)
                    except:
                        raise Exception, '%s create_entries: error no %s field' % (self.item_name, field_name)
                else:
                    field_list.append(None)
        else:
            field_list = self.fields
            field_list = [field for field in field_list if field.edit_visible and field.edit_index >= 0]
            field_list = sorted(field_list, key=lambda field: field.edit_index)
        if len(field_list):
            table = gtk.Table(1, 1, homogeneous)
            container.add(table)
            if label_on_top:
                table.set_row_spacings(0)
            else:
                table.set_row_spacings(row_spacings)
            table.set_col_spacings(col_spacings)
            table.resize(len(field_list) / col_count, col_count)
            for i, field in enumerate(field_list):
                if field:
                    field.create_entry(i, table, col_count, label_on_top, sel_from_view_form=sel_from_view_form,
                        sel_from_dropdown_box=sel_from_dropdown_box)
            table.show_all()

    def create_table_grid(self, container, detail, create_buttons=True, dblclick_edit=True, create_copy_button=False, button_width=100, button_padding=1):

        def add_button(caption, from_attr, action):
            button = gtk.Button(caption)
            button.set_size_request(button_width, -1)
            if action:
                button.connect('clicked', action)
            if self.edit_form:
                self.edit_form.__dict__[from_attr] = button
            return button

        vbox = gtk.VBox(False, 6)
        grid = DBGrid(detail, dblclick_edit=dblclick_edit)
        grid.set_size_request(300, 250)
        vbox.pack_start(grid, True, True, 0)

        if create_buttons:
            hseparator = gtk.HSeparator()
            vbox.pack_start(hseparator, False, False)

            hbox = gtk.HBox(False, 0)
            hbox.pack_start(add_button(self.task.lang['delete'], '%s_delete_button' % detail.item_name, detail.delete_record), False, padding=button_padding)
            hbox.pack_end(add_button(self.task.lang['new'], '%s_new_button' % detail.item_name, detail.append_record), False, padding=button_padding)
            hbox.pack_end(add_button(self.task.lang['edit'], '%s_edit_button' % detail.item_name, detail.edit_record), False, padding=button_padding)
            if create_copy_button:
                hbox.pack_end(add_button(self.task.lang['copy'], '%s_copy_button' % detail.item_name, detail.copy_record), False, padding=button_padding)
            vbox.pack_start(hbox, False, True, 0)
        vbox.show_all()
        container.add(vbox)
        return grid

    def create_table_grids(self, container, create_buttons = True, dblclick_edit = True, create_copy_button=False, button_width=100, button_padding=6):

        def tab_clicked(nb, page, page_num):
            if dblclick_edit:
                i = 0
                for detail in self.details:
                    if detail.visible:
                        if i == page_num:
                            self.active_detail = detail
                            break
                        i += 1

        self.active_detail = None
        detail_count = 0
        for detail in self.details:
            if detail.visible:
                detail_count += 1
        if detail_count > 0:
            if detail_count == 1:
                cur_detail = None
                for detail in self.details:
                    if detail.visible:
                        cur_detail = detail
                if cur_detail:
                    self.create_table_grid(container, cur_detail, create_buttons, dblclick_edit, create_copy_button)
                    if dblclick_edit:
                        self.active_detail = cur_detail
            else:
                notebook = gtk.Notebook()
                for table in self.details:
                    if table.visible:
                        frame = gtk.Frame('')
                        frame.set_border_width(10)
                        vbox = gtk.VBox()
                        frame.add(vbox)
                        self.create_table_grid(vbox, table, create_buttons, dblclick_edit)
                        label = gtk.Label(table.item_caption)
                        notebook.append_page(frame, label)
                container.add(notebook)
                notebook.connect('switch-page', tab_clicked)
                notebook.show_all()

    def create_edit_form(self, parent):
        self.edit_form = ItemWindow(self, self.edit_ui, parent)
        self.edit_form.window.connect('delete-event', self.check_edit)
        self.edit_form.window.connect("key-press-event", self.edit_keypressed)
        if self.task.on_before_show_edit_form:
            self.task.on_before_show_edit_form(self)
        if self.owner.on_before_show_edit_form:
            self.owner.on_before_show_edit_form(self)
        if self.on_before_show_edit_form:
            self.on_before_show_edit_form(self)
        self.edit_form.show()
        if self.task.on_after_show_edit_form:
            self.task.on_after_show_edit_form(self)
        if self.owner.on_after_show_edit_form:
            self.owner.on_after_show_edit_form(self)
        if self.on_after_show_edit_form:
            self.on_after_show_edit_form(self)
        #~ for detail in self.details:
            #~ if self.details_active:
                #~ detail.update_controls(common.UPDATE_OPEN)
            #~ else:
                #~ if not detail.disabled:
                    #~ detail.open()
        if self.edit_form.window:
            self.edit_form.window.connect("destroy", self.do_on_destroy_edit_form)

    def do_on_destroy_edit_form(self, window):
        if self.on_destroy_edit_form:
            self.on_destroy_edit_form(self)

    def edit_keypressed(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            if self.edit_form.window:
                focused = self.edit_form.window.get_focus()
                if isinstance(focused, gtk.Entry):
                    parent = focused.get_parent()
                    if isinstance(parent, DBEntry):
                        if parent.modified():
                            parent.cancel_edit()
                            return True
            self.check_edit(widget, event)
        if self.task.on_edit_keypressed:
            self.task.on_edit_keypressed(self, event)
        if self.owner.on_edit_keypressed:
            self.owner.on_edit_keypressed(self, event)
        if self.on_edit_keypressed:
            self.on_edit_keypressed(self, event)

    def grid_selected(self):
        for control in self.controls:
            if isinstance(control, DBGrid):
                return control.is_selected()

    def insert_record(self, widget):
        if self.can_create():
            if self.item_state == common.STATE_EDIT:
                self.post()
            if self.item_state != common.STATE_INSERT:
                self.insert()
            self.create_edit_form(widget)

    def append_record(self, widget):
        if self.can_create():
            if self.item_state == common.STATE_EDIT:
                self.post()
            if self.item_state != common.STATE_INSERT:
                self.append()
            self.create_edit_form(widget)

    def copy_record(self, widget):
        if self.can_create() and self.record_count():
            if not self.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                self.copy_rec()
                self.create_edit_form(widget)

    def edit_record(self, widget):
        if self.can_edit():
            if self.record_count() > 0:
                if not self.item_state in (common.STATE_INSERT, common.STATE_EDIT):
                    self.edit()
                self.create_edit_form(widget)

    def delete_record(self, widget):
        rec_no = self.rec_no
        record = self._records[rec_no]
        if not self.read_only:
            if self.can_delete():
                if self.grid_selected():
                    if self.record_count() > 0:
#                    if self.item_state == common.STATE_BROWSE and self.record_count() > 0:
                        if self.question(self.task.lang['delete_record']):
                            self.delete()
                            try:
                                self.apply()
                            except Exception, e:
                                self._records.insert(rec_no, record)
                                self._cur_row = rec_no
                                self.change_log.remove_record_log();
                                self.update_controls(common.UPDATE_RESTORE)
                                self.do_after_scroll()
                                error = e.message.upper()
                                if (error.find('FOREIGN KEY') != -1 and (error.find('VIOLATION') != -1 or error.find('FAILED'))):
                                    self.warning(self.task.lang['cant_delete_used_record'])
                                else:
                                    self.warning(e.message)

                else:
                    self.warning(u'Record is not selected.')

    def post_record(self, widget = None):

        if self.edit_form.window:
            focused = self.edit_form.window.get_focus()
            if isinstance(focused, gtk.Entry):
                parent = focused.get_parent()
                if isinstance(parent, DBEntry):
                    if not parent.change_field_text():
                        return
            try:
                self.check_record_valid()
            except Exception, e:
                self.show_invalid_mess(e.message)
                print traceback.format_exc()
                return False

            if self.modified:
                try:
                    self.post()
                    self.close_edit_form()
                except Exception, e:
                    self.show_invalid_mess(e.message)
                    print traceback.format_exc()
            else:
                self.cancel()
                self.close_edit_form()
                return True

    def apply_record(self, widget = None):

        if self.edit_form.window:
            focused = self.edit_form.window.get_focus()
            if isinstance(focused, gtk.Entry):
                parent = focused.get_parent()
                if isinstance(parent, DBEntry):
                    if not parent.change_field_text():
                        return
            try:
                self.check_record_valid()
            except Exception, e:
                self.show_invalid_mess(e.message)
                print traceback.format_exc()
                return False

            if self.modified:
                if self.is_changing():
                    if self.post():
                        self.apply()
                        self.close_edit_form()
                        return True
            else:
                self.close_edit_form()
                self.cancel()
                return True

    def cancel_edit(self, widget = None):
        self.close_edit_form()
        self.cancel()

    def create_filter_entries(self, container, filters=None, col_count=1, label_on_top=False, row_spacings=6, col_spacings=6, homogeneous=True,
            sel_from_view_form=True, sel_from_dropdown_box=False):
        children = container.get_children()
        for child in list(children):
            container.remove(child)
            child.destroy()
        if filters:
            filter_list = []
            for filter_name in filters:
                if filter_name:
                    filter_list.append(self.filter_by_name(filter_name))
                else:
                    filter_list.append(None)
        else:
            filter_list = [filter for filter in self.filters if filter.visible]
        if len(filter_list):
            table = gtk.Table(1, 1, homogeneous)
            container.add(table)
            if label_on_top:
                table.set_row_spacings(0)
            else:
                table.set_row_spacings(row_spacings)
            table.set_col_spacings(col_spacings)
            table.resize(len(filter_list) / col_count, col_count)
            for i, filter in enumerate(filter_list):
                if filter:
                    filter.field.create_entry(i, table, col_count, label_on_top, filter.filter_caption, sel_from_view_form=sel_from_view_form,
                        sel_from_dropdown_box=sel_from_dropdown_box)
            table.show_all()

    def create_filter_form(self, widget):
        if self.item_state == common.STATE_BROWSE:
            self.filter_form = ItemWindow(self, self.filter_ui, widget)
            if self.task.on_before_show_filter_form:
                self.task.on_before_show_filter_form(self)
            if self.owner.on_before_show_filter_form:
                self.owner.on_before_show_filter_form(self)
            if self.on_before_show_filter_form:
                self.on_before_show_filter_form(self)
            self.filter_form.show()
            if self.on_after_show_filter_form:
                self.on_after_show_filter_form(self)


    def apply_filter(self, widget):
        self.open()
        self.close_filter_form()

    def close_filter(self, widget):
        self.close_filter_form()

    def get_status_text(self, markup = False):
        text = self.task.lang['filter'] + ': '
        for fltr in self.filters:
            if fltr.visible and fltr.value:
                if fltr.field.data_type == common.BOOLEAN:
                    if fltr.value:
                        text += fltr.filter_caption + ' '
                else:
                    text += '%s: %s ' % (fltr.filter_caption, fltr.field.display_text)
        return text

    def get_window(self):
        if self.item_state == common.STATE_BROWSE:
            if self.view_form:
                if self.view_form.window:
                    return self.view_form.window
        else:
            if self.edit_form:
                if self.edit_form.window:
                    return self.edit_form.window
        if self.task.main_form:
            if self.task.main_form.window:
                return self.task.main_form.window

    def question(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        result = question(win, message)
        if result == gtk.RESPONSE_YES:
            return True

    def warning(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        return warning(win, message)

    def error(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        return error(win, message)

    def yes_no_cancel(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        result = yes_no_cancel(win, message)
        if result == gtk.RESPONSE_YES:
            return 1
        elif result == gtk.RESPONSE_NO:
            return 0
        elif result == gtk.RESPONSE_CANCEL:
            return -1
        return result

    def can_view(self):
        return self.task.has_privilege(self, 'can_view')

    def can_create(self):
        return self.task.has_privilege(self, 'can_create')

    def can_edit(self):
        return self.task.has_privilege(self, 'can_edit')

    def can_delete(self):
        return self.task.has_privilege(self, 'can_delete')


class ReportInterface(object):
    def __init__(self):
        self.on_before_show_params_form = None
        self.on_after_show_params_form = None
        self.on_destroy_params_form = None
        self.on_before_print_report = None
        self.on_after_print_report = None
        self.on_print_report = None
        self.on_param_lookup_item_show = None
        self.extension = None

    def create_params_form(self, widget):
        self.params_form = ItemWindow(self, self.edit_ui, widget)
        self.params_form.window.connect("key-press-event", self.edit_keypressed)
        if self.task.on_before_show_params_form:
            self.task.on_before_show_params_form(self)
        if self.owner.on_before_show_params_form:
            self.owner.on_before_show_params_form(self)
        if self.on_before_show_params_form:
            self.on_before_show_params_form(self)
        self.params_form.show()
        if self.on_after_show_params_form:
            self.on_after_show_params_form(self)
        if self.params_form.window:
            self.params_form.window.connect("destroy", self.do_on_destroy_params_form)

    def do_on_destroy_params_form(self, window):
        if self.on_destroy_params_form:
            self.on_destroy_params_form(self)

    def edit_keypressed(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.close_form(widget)

    def check_params(self):
        try:
            for param in self.params:
                param.check_valid()
            return True
        except Exception, e:
            self.warning(u'Параметр %s: %s' % (param.param_caption, e.args[0]))
            return False

    def print_report(self, widget = None):
        show_form = False
        for param in self.params:
            if param.edit_visible:
                show_form = True
        if show_form:
            self.create_params_form(widget)
        else:
            self.process_report()

    def process_report(self, widget = None):
        try:
            if self.check_params():
                if self.owner.on_before_print_report:
                    self.owner.on_before_print_report(self)
                if self.on_before_print_report:
                    self.on_before_print_report(self)
                url = self.send_to_server()
                if self.on_print_report:
                    self.on_print_report(self, url)
                elif self.owner.on_print_report:
                    self.owner.on_print_report(self, url)
                else:
                    self.task.open_file(url)
                if self.on_after_print_report:
                    self.on_after_print_report(self)
                return True
        except Exception, e:
            self.show_invalid_mess(e.message)
            print traceback.format_exc()

    def close_form(self, widget):
        if self.params_form:
            if self.params_form.window:
                self.params_form.window.destroy()
                self.params_form = None

    def edit_params(self, container, params=None, col_count=1, label_on_top=False, row_spacings=6, col_spacings=6):
        children = container.get_children()
        for child in list(children):
            container.remove(child)
            child.destroy()
        if params:
            param_list = []
            for param_name in params:
                if param_name:
                    try:
                        param_list.append(self.param_by_name(param_name))
                    except:
                        raise Exception, '%s create_entries: error no %s param' % (self.item_name, param_name)
                else:
                    param_list.append(None)
        else:
            param_list = [param for param in self.params if param.edit_visible]
        if len(param_list):
            table = gtk.Table(1, 1, True)
            container.add(table)
            if label_on_top:
                table.set_row_spacings(0)
            else:
                table.set_row_spacings(row_spacings)
            table.set_col_spacings(col_spacings)
            table.resize(len(param_list) / col_count, col_count)
            for i, param in enumerate(param_list):
                if param and param.edit_visible:
                    param.create_entry(i, table, col_count, label_on_top)
            table.show_all()

    def get_window(self):
        if self.params_form:
            if self.params_form.window:
                return self.params_form.window

    def show_invalid_mess(self, mess):
        if type(mess) == tuple:
            mess = mess[0]
        if self.params_form:
            if self.error_label:
                try:
                    self.error_label.set_markup('<span color="firebrick">%s</span>' % mess)
                except:
                    if mess:
                        self.warning(mess)
            elif mess:
                    self.warning(mess)
        else:
            if mess:
                print mess

    def warning(self, message, widget=None):
        if widget:
            win = get_widget_window(widget)
        else:
            win = self.get_window()
        if win:
            return warning(win, message)

    def can_view(self):
        return self.task.has_privilege(self, 'can_view')

    def can_create(self):
        return self.task.has_privilege(self, 'can_create')

    def can_edit(self):
        return self.task.has_privilege(self, 'can_edit')

    def can_delete(self):
        return self.task.has_privilege(self, 'can_delete')

class Window(object):
    def __init__(self, ui, caption, widget):
        self.caption = caption
        if ui:
            self.builder = gtk.Builder()
            self.builder.add_from_string(ui)
            self.window = self.window1
        else:
            self.builder = None
            self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(caption)
        self.window.owner = self
        parent_window = get_widget_window(widget)
        if parent_window:
            self.window.set_transient_for(parent_window)
            self.window.set_modal(True)

    def show(self):
        if self.window:
            if not self.window.get_visible():
                self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
                self.window.show()

    def close(self):
        self.window.destroy()

    def no_builder_message(self):
        '%s: there is no ui form' % self.caption

    def __getattr__(self, attr):
        if self.builder:
            obj = self.builder.get_object(attr)
            if obj:
                setattr(self, attr, obj)
            else:
                raise AttributeError (' AttributeError: ' + attr)
            return obj
        else:
            raise RuntimeError('%s: there is not ui form' % self.caption)


class ItemWindow(Window):
    def __init__(self, item, ui, widget):
        Window.__init__(self, ui, item.item_caption, widget)
        self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.item = item


class MainWindow(Window):
    def __init__(self, item, ui):
        Window.__init__(self, ui, item.item_caption, None)
        self.item = item
        self.item.window = self
        self.item.main_form = self
        self.window.connect("destroy", self.do_on_destroy)

    def do_on_destroy(self, window):
        self.item.do_on_destroy_form()
        gtk.main_quit()

    def tray_menu_right_click_event(self, icon, button, time):
        if self.item.tray_info['menu']:
            self.item.tray_info['menu'].popup(None, None, gtk.status_icon_position_menu, button, time, self.tray_icon)

    def show(self):
        self.window.show()
        self.window.set_accept_focus(True)
        self.window.grab_focus()
        self.item.tray_icon = None
        if self.item.tray_info:
            self.has_appindicator = True
            try:
                import appindicator
            except:
                self.has_appindicator = False
            if self.has_appindicator:
                tray_icon = appindicator.Indicator(self.item.item_name, self.item.tray_info['caption'], appindicator.CATEGORY_APPLICATION_STATUS)
                tray_icon.set_status (appindicator.STATUS_ACTIVE)
                tray_icon.set_attention_icon ("indicator-messages-new")
                tray_icon.set_icon(self.item.tray_info['image'])
                tray_icon.set_menu(self.item.tray_info['menu'])
            else:
                tray_icon = gtk.StatusIcon()
                tray_icon.set_from_stock(self.item.tray_info['image'])
                tray_icon.connect('popup-menu', self.tray_menu_right_click_event)
                tray_icon.set_tooltip(self.item.tray_info['caption'])
            self.tray_icon = tray_icon
        gtk.main()


class DBEntry(gtk.HBox):
    def __init__(self, field, sel_from_view_form=True, sel_from_dropdown_box=False):
        gtk.HBox.__init__(self, False, 0)
        self.field = field
        field.controls.append(self)
        self.connect("destroy", self.do_on_destroy)
        self.select_from_view_form_button = None
        self.entry = None
        self.check_button = None
        self.combobox = None
        self.invalid_text = False
        self.label = None
        self.sel_from_view_form = sel_from_view_form
        self.sel_from_dropdown_box = sel_from_dropdown_box
        self.updating = False
        if self.field.lookup_item:
            self.entry = gtk.Entry()
            self.pack_start(self.entry)
            self.entry.set_icon_from_stock(0, gtk.STOCK_CLEAR)
            self.entry.set_icon_from_stock(1, gtk.STOCK_OPEN)
            if sel_from_view_form and sel_from_dropdown_box:
                self.select_from_view_form_button = self.add_button('...', self.button_clicked)
                self.entry.connect("key-press-event", self.entry_keypressed)
                self.entry.connect("icon_press", self.icon_pressed)
            elif sel_from_view_form or sel_from_dropdown_box:
                self.entry.connect("key-press-event", self.entry_keypressed)
                self.entry.connect("icon_press", self.icon_pressed)
        elif (self.field.data_type == common.DATE) or (self.field.data_type == common.DATETIME):
            self.entry = gtk.Entry()
            self.entry.set_icon_from_stock(1, gtk.STOCK_OPEN)
            self.pack_start(self.entry, False, False)
            self.entry.connect("key-press-event", self.entry_keypressed)
            self.entry.connect("icon_press", self.icon_pressed)
        elif (self.field.data_type == common.INTEGER) and self.field.value_list:
            self.combobox = gtk.combo_box_new_text()
            for val in self.field.value_list:
                self.combobox.append_text(val)
            self.combobox.set_property('active', field.value - 1)
            self.combobox.connect("changed", self.combobox_changed)
            self.pack_start(self.combobox)
        elif (self.field.data_type == common.BOOLEAN):
            self.check_button = gtk.CheckButton()
            self.check_button.connect("toggled", self.button_toggled)
            self.pack_start(self.check_button, False, False)
        else:
            self.entry = gtk.Entry()
            self.entry.connect("key-press-event", self.entry_keypressed)
            if self.field.data_type != common.TEXT:
                self.pack_start(self.entry, False, False)
            else:
                self.pack_start(self.entry)
        if self.entry:
            self.entry.set_property('xalign', self.field.xalign())
            self.entry.connect('focus-in-event', self.on_enter_entry)
            self.entry.connect_after('focus-out-event', self.on_exit_entry)
            self.entry.connect('button-release-event', self.mouse_up)
            self.entry.owner = self
        self.update()

    def update(self):
        if self.entry:
            alignment = self.entry.get_property('xalign')
            if alignment != self.field.alignment:
                self.entry.set_property('xalign', self.field.xalign())
            if self.select_from_view_form_button:
                self.select_from_view_form_button.set_sensitive(not self.field.read_only)
            self.entry.set_editable(not self.field.read_only)
            self.entry.set_sensitive(not self.field.read_only and not self.field.master_field)
            self.entry.modify_text(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse("gray30"))
#            self.entry.modify_base(gtk.STATE_INSENSITIVE, gtk.gdk.color_parse("white smoke"))
            if self.field.lookup_item:
                if self.field.read_only or self.field.master_field:
                    self.entry.set_icon_from_stock(0, None)
                    self.entry.set_icon_from_stock(1, None)
                else:
                    self.entry.set_icon_from_stock(0, gtk.STOCK_CLEAR)
                    self.entry.set_icon_from_stock(1, gtk.STOCK_OPEN)
            if (self.field.data_type == common.DATE) or (self.field.data_type == common.DATETIME):
                if self.field.read_only:
                    self.entry.set_icon_from_stock(1, None)
                else:
                    self.entry.set_icon_from_stock(1, gtk.STOCK_OPEN)
            self.entry.set_text(self.field.display_text)
        if self.check_button:
            self.check_button.set_active(self.field.value)
            self.check_button.set_sensitive(not self.field.read_only)
        if self.combobox:
            self.combobox.set_property('active', self.field.value - 1)
            self.combobox.set_sensitive(not self.field.read_only)


    def do_on_destroy(self, widget):
        self.field.controls.remove(self)

    def add_button(self, caption, action):
        button = gtk.Button(caption)
        button.set_can_focus(False)
        button.connect('clicked', action)
        self.pack_start(button, False, False)
        return button

    def button_toggled(self, toggle_button):
        self.field.value = toggle_button.get_active()

    def modified(self):
        if self.entry.get_text() != self.field.display_text:
            return True

    def cancel_edit(self):
        if self.field.lookup_item:
            self.entry.set_text(self.field.display_text)
        else:
            self.entry.set_text(self.field.text)
        self.field.show_invalid_mess('')
        self.field.show_error_mark(False)

    def button_clicked(self, widget):
        if self.field.on_entry_button_click:
            self.field.on_entry_button_click(widget, self.field)
        else:
            self.field.select_from_view_form(widget)

    def entry_keypressed(self, widget, event):
        if event.keyval == gtk.keysyms.Return:
            if self.field.lookup_item:
                self.entry.grab_focus()
                text = self.entry.get_text()
                if text == self.field.display_text:
                    text = ''
                if self.sel_from_view_form and self.sel_from_dropdown_box:
                    if event.state & gtk.gdk.CONTROL_MASK:
                        if self.field.on_entry_button_click:
                            self.field.on_entry_button_click(widget, self.field)
                        else:
                            self.field.select_from_view_form(widget)
                    else:
                        if self.field.on_entry_drop_down_click:
                            self.field.on_entry_drop_down_click(widget, self.field)
                        else:
                            self.field.select_from_dropdown_box(widget, search=text)
                elif self.sel_from_dropdown_box:
                    if self.field.on_entry_drop_down_click:
                        self.field.on_entry_drop_down_click(widget, self.field)
                    else:
                        self.field.select_from_dropdown_box(widget, search=text)
                elif self.sel_from_view_form:
                    if self.field.on_entry_drop_down_click:
                        self.field.on_entry_drop_down_click(widget, self.field)
                    else:
                        self.button_clicked(widget)
            elif (self.field.data_type == common.DATE) or (self.field.data_type == common.DATETIME):
                self.entry.grab_focus()
                self.field.show_calender(widget)
        elif event.keyval == gtk.keysyms.Tab or event.keyval == gtk.keysyms.ISO_Left_Tab:
            if not self.change_field_text():
                return True
        if not self.field.lookup_item:
            if self.field.data_type in (common.INTEGER, common.FLOAT, common.CURRENCY, common.DATE, common.DATETIME):
                pressed_key = key_pressed(event)
                if pressed_key:
                    if self.field.data_type == common.INTEGER:
                        if not (pressed_key.isdigit() or pressed_key in ('-', '+')):
                            return True
                    if self.field.data_type in (common.FLOAT, common.CURRENCY):
                        if not (pressed_key.isdigit() or pressed_key in ('.', common.DECIMAL_POINT, '-', '+', 'e', 'E')):
                            return True

    def icon_pressed(self, widget, icon_pos, event):
        if not self.field.read_only:
            if (self.field.data_type == common.DATE) or (self.field.data_type == common.DATETIME):
                if self.field.on_entry_drop_down_click:
                    self.field.on_entry_drop_down_click(widget, self.field)
                else:
                    self.entry.grab_focus()
                    self.field.show_calender(widget)
            elif self.field.lookup_item:
                self.entry.grab_focus()
                if icon_pos == 0:
                    if self.field.on_entry_clear_click:
                        self.field.on_entry_clear_click(widget, self.field)
                    else:
                        self.field.set_value(None)
                else:
                    if (self.sel_from_view_form and self.sel_from_dropdown_box) or self.sel_from_dropdown_box:
                        if self.field.on_entry_drop_down_click:
                            self.field.on_entry_drop_down_click(widget, self.field)
                        else:
                            self.field.select_from_dropdown_box(widget)
                    elif self.sel_from_view_form:
                        self.button_clicked(widget)

    def combobox_changed(self, widget):
        text = self.combobox.get_active_text()
        try:
            self.field.value = self.field.value_list.index(text) + 1
        except:
            self.field.value =  None

    def change_field_text(self):
        result = True
        if self.updating:
            return
        self.updating = True
        try:
            if self.entry:
                self.field.show_error_mark('')
                if not self.field.lookup_item:
                    try:
                        text = self.entry.get_text()
                        if (text == ''):# and not self.field.value:
                            self.field.value = None
                        else:
                            self.field.text = text
                            self.field.check_valid()
                            self.field.show_invalid_mess('')
                            self.field.show_error_mark('')
                            self.entry.set_text(text)
                    except Exception, e:
                        self.invalid_text = True
                        try:
                            self.entry.grab_focus()
                            self.entry.select_region(0, -1)
                            self.field.show_invalid_mess(e.message)
                            self.field.show_error_mark(True)
                        finally:
                            self.invalid_text = False
                        result = False
                        print traceback.format_exc()
                else:
                    if self.entry.get_text() != self.field.lookup_text:
                        self.entry.set_text(self.field.display_text)
        finally:
            self.updating = False
        return result

    def mouse_up(self, widget, event):
        pass
#        self.entry.select_region(0, -1)

    def on_enter_entry(self, widget, param1):
        if not self.invalid_text:
            if not self.field.lookup_item:
                self.entry.set_text(self.field.text)
            else:
                self.entry.set_text(self.field.display_text)

    def on_exit_entry(self, widget, param1):
        if self.change_field_text():
            self.entry.set_text(self.field.display_text)


class ListGrid(gtk.ScrolledWindow):
    def __init__(self, def_list, items_list, border_width = 6):
        gtk.ScrolledWindow.__init__(self)
        self.set_border_width(border_width)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.grid = gtk.TreeView()
        self.add(self.grid)
        self.def_list = def_list
        self.items_list = items_list
        self.refresh()

    def create_column(self, def_item, index):

        def on_toggled(widget, path, index):
            model = self.grid.get_model()
            model[path][index] = not model[path][index]
        if def_item['type'] == bool:
            cell = gtk.CellRendererToggle()
            cell.connect("toggled", on_toggled, index)
            column = gtk.TreeViewColumn(def_item['caption'], cell, active=index)
        else:
            cell = gtk.CellRendererText()
            column = gtk.TreeViewColumn(def_item['caption'], cell, markup = index)
        column.set_widget(gtk.Label())
        column.get_widget().set_markup(u'<small><b>' + def_item['caption'] + '</b></small>')
        if not def_item['caption']:
            column.set_visible(False)
        column.set_alignment(0.5)
        column.get_widget().show()
        column.set_resizable(True)
        if index == 1:
            column.set_expand(True)
        self.grid.append_column(column)
        return column

    def fill_store(self):
        for item in self.items_list:
            self.store.append(list(item))

    def refresh(self):
        types = []
        for i, def_item in enumerate(self.def_list):
            self.create_column(def_item, i)
            types.append(def_item['type'])
        self.store = gtk.ListStore(*types)
        self.fill_store()
        self.grid.set_model(self.store)

        if len(self.store):
            path = self.store[0].path
            self.select_row(path)

    def select_row(self, path):
        self.grid.scroll_to_cell(path)
        selection = self.grid.get_selection()
        if selection:
            selection.select_path(path)

    def get_row_iter(self):
        selection = self.grid.get_selection()
        if selection:
            model, iter = selection.get_selected()
            return iter

    def path_by_iter(self, iter):
        return int(self.store.get_string_from_iter(iter))

    def selected_index(self):
        return self.path_by_iter(self.get_row_iter())

    def remove_row(self, iter):
        path = self.path_by_iter(iter)
        self.store.remove(iter)
        if path >= len(self.store):
            path -= len(self.store) - 1
        if len(self.store):
            self.select_row(path)

    def add_row(self, store, iter):
        row = []
        min_index = min(store.get_n_columns(), self.store.get_n_columns())
        for i in range(min_index):
            row.append(store.get(iter, i)[0])
        col_count = self.store.get_n_columns()
        if len(row) < col_count:
            for i in range(len(row), col_count):
                row.append(None)
        new_iter = self.store.append(row)
        self.select_row(self.path_by_iter(new_iter))

    def swap_row(self, iter, direction):
        path1 = self.path_by_iter(iter)
        path2 = path1 + direction
        if path2 >= 0 and path2 < len(self.store):
            self.store.swap(self.store.get_iter(path1), self.store.get_iter(path2))


class DBGrid(gtk.ScrolledWindow):
    def __init__(self, dataset, fields=None, dblclick_edit=True, headers=True, lines=False,
        border_width=6, striped=True, on_dblclick=None, multi_select=False,
        multi_select_get_selected=None, multi_select_set_selected=None):
        gtk.ScrolledWindow.__init__(self)
        self.set_border_width(border_width)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.grid = gtk.TreeView()
        self.grid.add_events(gtk.gdk.KEY_PRESS_MASK)
        if striped:
            self.grid.set_rules_hint(True)
        self.add(self.grid)
        self.dataset = dataset
        self.multi_select = multi_select
        self.multi_select_get_selected = multi_select_get_selected
        self.multi_select_set_selected = multi_select_set_selected
        if self.dataset.is_lookup_item and not self.dataset.lookup_selected_ids is None:
            self.multi_select = True
            self.multi_select_get_selected = self.lookup_get_selected
            self.multi_select_set_selected = self.lookup_set_selected
        self.field_indexes = {}
        self.headers = headers
        self.lines = lines
        if fields is None:
            self.fields = sorted(self.dataset.fields, key=lambda field: field.view_index)
        else:
            self.fields = [dataset.field_by_name(field) for field in fields]
        dataset.controls.append(self)
        self.dblclick_edit = dblclick_edit
        self.on_dblclick = on_dblclick
        self.grid.connect('row-activated', self.do_on_dblclicked)
        self.grid.connect('cursor-changed', self.do_on_cursor_changed)
        self.grid.connect('size-allocate', self.do_on_resize)
        self.grid.connect("move-cursor", self.do_on_move_cursor)
        self.grid.connect("destroy", self.do_on_destroy)
        self.grid.connect("key-press-event", self.key_pressed)
        self.grid.connect("key-release-event", self.key_released)
        v_adjustment = self.get_vadjustment()
        v_adjustment.connect("value-changed", self.v_adj_value_changed)
        self.cell_height = 0
        self.on_record_changed = None
        self.on_draw_cell = None
        self.update_dataset = True
        self.cur_width = 0
        self.proportional_wrapping = True
        if self.dataset.active:
            self.refresh()

    def lookup_get_selected(self, dataset):
        return dataset.lookup_selected_ids.get(dataset.id.value)

    def lookup_set_selected(self, dataset, value):
        if value:
            dataset.lookup_selected_ids[dataset.id.value] = True
        else:
            if dataset.lookup_selected_ids.get(dataset.id.value):
                del dataset.lookup_selected_ids[dataset.id.value]

    def get_field_index(self, field):
        index = self.field_indexes.get(field)
        if index:
            return index
        else:
            return -1

    def register_field(self, field, index):
        self.field_indexes[field] = index

    def do_on_destroy(self, widget):
        self.dataset.controls.remove(self)

    def refresh_field(self, model, iter, field):
        if iter:
            try:
                if self.get_field_index(field) >= 0:
                    if field.data_type == common.BOOLEAN:
                        model[iter][self.get_field_index(field)] = field.value
                    else:
                        model[iter][self.get_field_index(field)] = escape(field.display_text)
            except Exception, e:
                print 'refresh_field', field.field_name, self.get_field_index(field), e.message

    def update_field(self, field):
        if self.dataset.controls_enabled():
            model = self.grid.get_model()
            if model:
                iter = self.find_rec_iter()
                self.refresh_field(model, iter, field)

    def find_rec_iter(self):
        model = self.grid.get_model()
        if model:
            info = self.dataset.rec_controls_info()
            if info:
                iter = info.get(self)
                if iter and model.iter_is_valid(iter):
                    return iter

    def syncronize(self):
        if self.dataset.record_count() > 0:
            model = self.grid.get_model()
            iter = self.find_rec_iter()
            self.select_iter(iter)
            for field in self.fields:
                self.refresh_field(model, iter, field)

    def select_iter(self, iter):
        model = self.grid.get_model()
        if iter and model and model.iter_is_valid(iter):
            try:
                path = model.get_path(iter)
                self.grid.scroll_to_cell(path)
                selection = self.grid.get_selection()
                if selection:
                    selection.select_path(path)
            except:
                pass

    def update(self, state):

        def update_grid(iter):
            self.select_iter(iter)

        if state == common.UPDATE_OPEN:
            self.refresh()
        elif state == common.UPDATE_SCROLLED:
            if self.dataset.controls_enabled():
                self.syncronize()
        elif state == common.UPDATE_DELETE:
            model = self.grid.get_model()
            iter = self.find_rec_iter()
            if iter:
                model.remove(iter)
        elif state == common.UPDATE_CANCEL:
            if (self.dataset.record_count() > 0) and self.grid.get_model():
                model = self.grid.get_model()
                iter = self.find_rec_iter()
                for field in self.fields:
                    self.refresh_field(model, iter, field)
                update_grid(iter)
        elif state == common.UPDATE_APPEND:
            model = self.grid.get_model()
            iter = self.append_row(model)
            update_grid(iter)
        elif state == common.UPDATE_INSERT:
            model = self.grid.get_model()
            iter = self.insert_row(model)
            update_grid(iter)
        elif state == common.UPDATE_RESTORE:
            iter = self.restore_row()
            update_grid(iter)
        elif state == common.UPDATE_REFRESH:
            self.refresh()

    def key_released(self, widget, event):
        if event.keyval in (gtk.keysyms.Down, gtk.keysyms.Up,
            gtk.keysyms.Page_Up, gtk.keysyms.Page_Down):
            self.update_dataset = True
            self.do_on_cursor_changed(self.grid)

    def key_pressed(self, widget, event):
        if event.keyval in (gtk.keysyms.Down, gtk.keysyms.Up,
            gtk.keysyms.Page_Up, gtk.keysyms.Page_Down):
            self.update_dataset = False

    def resize_columns(self):

        def get_title_width(column):
            result = 0
            if column.field:
                label = column.get_widget()
                layout = label.get_layout()
                title = column.get_title()
                if column.field:
                    title = column.field.field_caption
                layout.set_markup(u'<small><b>' + title + '</b></small>')
                result = layout.get_pixel_size()[0] + 12
            return result

        allocation = self.grid.get_allocation()
        columns = self.grid.get_columns()
        fixed_columns_width = 0
        wrap_columns_width = 0
        wrap_column_count = 0
        fixed_column_count = 0
        for column in columns:
            if column.get_visible():
                column.cur_width = max(column.cell_get_size()[3], get_title_width(column))
                if column.field:
                    if column.field.word_wrap and not column.field.wrap_width:
                        wrap_column_count += 1
                        wrap_columns_width += column.cur_width
                    else:
                        fixed_column_count += 1
                        if column.field.word_wrap and column.field.wrap_width:
                            fixed_columns_width += column.field.wrap_width
                        else:
                            fixed_columns_width += column.cur_width
        if wrap_column_count:
            for column in columns:
                if column.get_visible():
                    if column.field:
                        if column.field.word_wrap:
                            if not column.field.wrap_width:
                                if self.proportional_wrapping:
                                    wrap_cell_width = int((allocation.width - fixed_columns_width)  * (column.cur_width) / wrap_columns_width)
                                else:
                                    wrap_cell_width = int((allocation.width - fixed_columns_width) / wrap_column_count)
                                if wrap_cell_width < 50:
                                    wrap_cell_width = 50
                            else:
                                wrap_cell_width = column.field.wrap_width
                            column.set_property('max-width', wrap_cell_width)
                            column.set_property('min-width', wrap_cell_width)
                            cells = column.get_cell_renderers()
                            cells[0].set_property('wrap-mode', pango.WRAP_WORD_CHAR)#True)
                            cells[0].set_property('wrap-width', wrap_cell_width)
            model = self.grid.get_model()
            if model:
                iter = model.get_iter_first()
                while iter and model.iter_is_valid(iter):
                    model.row_changed(model.get_path(iter), iter)
                    iter = model.iter_next(iter)

    def do_on_resize(self, widget, allocation):
        self.check_to_load()

        columns = self.grid.get_columns()
        if len(columns): #and self.cur_width != allocation.width:
            self.cur_width = allocation.width
            self.resize_columns()

    def do_on_dblclicked(self, treeview, path, view_column):
        if path[0] < self.dataset.record_count():
            if self.dataset.lookup_field:
                self.dataset.set_lookup_field_value(treeview)
            else:
                if self.on_dblclick:
                    self.on_dblclick(self)
                elif self.dblclick_edit:
                    self.dataset.edit_record(treeview)


    def v_adj_value_changed(self, a):
        self.check_to_load()

    def do_on_move_cursor(self, treeview, step, count):
        if step.value_nick == 'buffer-ends' and count == 1:
            self.check_to_load(True)

    def do_on_cursor_changed(self, treeview):
        if self.update_dataset:
            model, iter = self.grid.get_selection().get_selected()
            self.check_to_load()
            if iter:
                row = model.get_value(iter, 0)
                if row:
                    sel_row = self.dataset._records.index(row)
                    self.dataset.rec_no = sel_row
                else:
                    if not self.dataset.is_loaded:
                        del model[-1]
                        recs = self.load_next()
                if self.on_record_changed:
                    self.on_record_changed(self)

    def check_to_load(self, all=False):
        if self.dataset.auto_loading and not self.dataset.is_loaded:
            if self.grid.flags() & gtk.REALIZED:
                model = self.grid.get_model()
                if model:
                    if all:
                        while True:
                            if not self.load_next():
                                return None
                    grid_rect = self.grid.get_visible_rect()
                    grid_height = grid_rect.height
                    if len(model) > 0:
                        iter = model.get_iter_from_string(str(len(model) - 1))
                        path = model.get_path(iter)
                        if self.cell_height == 0:
                            last_cell_rect = self.grid.get_cell_area(path, self.grid.get_columns()[0])
                            cell_bottom = last_cell_rect.y + last_cell_rect.height
                            cell_height = last_cell_rect.height
                        else:
                            cell_bottom = self.cell_height * len(model) - grid_rect.y
                            cell_height = self.cell_height
                        while cell_bottom <= 2 * grid_height + cell_height:
                            if self.load_next():
                                cell_bottom += cell_height * self.dataset.limit
                            else:
                                break
                        if self.cell_height == 0:
                            self.cell_height = cell_bottom / (len(model) + 1)

    def load_next(self):
        try:
            cur_rec_no = self.dataset.rec_no
            self.dataset.disable_controls()
            result = self.dataset.load_next()
            if result:
                model = self.grid.get_model()
                self.fill_store(model, next=True)
        finally:
            self.dataset.enable_controls()
            self.dataset.rec_no = cur_rec_no
        return result

    def is_selected(self):
        selection = self.grid.get_selection()
        if selection:
            model, row = selection.get_selected()
            if row:
                return True

    def activate_field_edit(self, field):
        if not self.dataset.read_only:
            if self.grid.is_focus():
                model, iter = self.grid.get_selection().get_selected()
                if iter:
                    path = model.get_path(iter)
                    column = self.grid.get_column(self.get_field_index(field))
                    self.grid.set_cursor_on_cell(path, column, start_editing=True)

    def on_toggled(self, widget, path):
        model = self.grid.get_model()
        iter = model.get_iter(path)
        row = model.get_value(iter, 0)
        sel_row = self.dataset._records.index(row)
        self.dataset.rec_no = sel_row
        model[path][1] = not model[path][1]
        if self.multi_select_set_selected:
            self.multi_select_set_selected(self.dataset, model[path][1])

    def on_field_toggled(self, widget, path, field):
        model = self.grid.get_model()
        iter = model.get_iter(path)
        row = model.get_value(iter, 0)
        sel_row = self.dataset._records.index(row)
        self.dataset.rec_no = sel_row
        if not (field.owner.item_state in (common.STATE_INSERT, common.STATE_EDIT)):
            field.owner.edit()
        model[path][self.get_field_index(field)] = not model[path][self.get_field_index(field)]
        field.value =  model[path][self.get_field_index(field)]

    def create_toggle_column(self, caption, index, field=None):
        cell = gtk.CellRendererToggle()
        if field:
            if field.editable:
                cell.connect("toggled", self.on_field_toggled, field)
        else:
            cell.connect("toggled", self.on_toggled)
        column = gtk.TreeViewColumn(caption, cell, active=index)
        column.set_widget(gtk.Label())
        column.get_widget().set_markup(u'<small><b>' + caption + '</b></small>')
        column.get_widget().show()
        column.set_alignment(0.5)
        column.field = field
        self.grid.append_column(column)
        return column

    def valid_field(self, field):
        return field.view_visible

    def field_edited(self, cell, iter, text, field):
        if not field.owner.read_only:
            try:
                if field.owner.item_state != common.STATE_EDIT:
                    field.owner.edit()
                field.text = text
                model = self.grid.get_model()
                model[iter][self.get_field_index(field)] = escape(field.display_text)
            except:
                pass

    def create_row_column(self):
        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('', cell)
        column.set_visible(False)
        column.field = None
        self.grid.append_column(column)
        return column

    def column_cell_func(self, column, cell, model, iter):
        if self.on_draw_cell:
            col_field = ''
            if column.field:
                col_field = column.field.field_name
            self.on_draw_cell(self, column, cell, model, iter, col_field)

    def create_column(self, field, index):
        cell = gtk.CellRendererText()
        cell.set_property('xalign', field.xalign())
        if field.editable:
            cell.set_property('editable', True)
            cell.connect('edited', self.field_edited, field)
        #~ if field.word_wrap:
            #~ cell.set_property('wrap-mode', True)
            #~ cell.set_property('wrap-width', 500)
        column = gtk.TreeViewColumn(field.field_name, cell, markup=index)
        column.field = field
        column.set_widget(gtk.Label())
        column.get_widget().set_markup(u'<small><b>' + field.field_caption + '</b></small>')
        column.set_alignment(0.5)
        column.get_widget().show()
        column.set_resizable(True)
        column.set_expand(field.expand)
        column.set_cell_data_func(cell, self.column_cell_func)
        self.grid.append_column(column)
        return column

    def create_store_row(self):
        row = []
        row.append(self.dataset._records[self.dataset.rec_no])
        if self.multi_select and self.multi_select_get_selected:
            value = self.multi_select_get_selected(self.dataset)
            row.append(value)
        for field in self.fields:
            if self.valid_field(field):
                if field.data_type == common.BOOLEAN:
                    row.append(field.value)
                else:
                    row.append(escape(field.display_text))
        return row

    def append_row(self, model):
        iter = model.append(self.create_store_row())
        info = self.dataset.rec_controls_info()
        info[self] = iter
        return iter

    def insert_row(self, model):
        iter = model.insert(0, self.create_store_row())
        info = self.dataset.rec_controls_info()
        info[self] = iter
        return iter

    def restore_row(self):
        model, iter = self.grid.get_selection().get_selected()
        new_row = self.create_store_row()
        if self.dataset.rec_no == len(self.dataset._records) - 1:
            new_iter = model.insert_after(iter, new_row)
        else:
            new_iter = model.insert_before(iter, new_row)
        info = self.dataset.rec_controls_info()
        info[self] = new_iter
        return new_iter

    def fill_store(self, store, next = False):
        rec_no = self.dataset.rec_no
        clone = self.dataset.clone()
        clone.on_get_field_text = self.dataset.on_get_field_text
        try:
            if next:
                row = store[-1][0]
                clone.rec_no = clone._records.index(row)
                clone.next()
                self.dataset._cur_row = clone.rec_no
            else:
                clone.first()
                self.dataset._cur_row = clone.rec_no
            while not clone.eof():
                self.append_row(store)
                clone.next()
                self.dataset._cur_row = clone.rec_no
        finally:
            self.dataset._cur_row = rec_no

    def refresh(self):
        self.sel_count = 0
        columns = self.grid.get_columns()
        for column in columns:
            self.grid.remove_column(column)

        self.create_row_column()
        i = 1
        if self.multi_select:
            self.create_toggle_column('', i)
            i += 1
        for field in self.fields:
            if self.valid_field(field):
                if field.data_type == common.BOOLEAN:
                    self.create_toggle_column(field.field_caption, i, field)
                else:
                    self.create_column(field, i)
                self.register_field(field, i)
                i += 1

        self.grid.set_headers_visible(self.headers)
        if self.lines:
            self.grid.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_BOTH)
        else:
            self.grid.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_NONE)

        types = []
        for field in self.fields:
            if self.valid_field(field):
                if field.data_type == common.BOOLEAN:
                    types.append(bool)
                else:
                    types.append(str)

        if self.multi_select:
            types = [bool] + types
        types = [object] + types

        self.store = gtk.ListStore(*types)
        self.dataset.disable_controls()
        try:
            self.fill_store(self.store)

            self.grid.set_model(self.store)

#            self.dataset.first()
        finally:
            self.dataset.enable_controls()
        self.cell_height = 0

    def path_by_iter(self, iter):
        return int(self.store.get_string_from_iter(iter))

    def move_up(self):
        selection = self.grid.get_selection()
        if selection:
            model, iter = selection.get_selected()
            self.swap_row(iter, -1)

    def move_down(self):
        selection = self.grid.get_selection()
        if selection:
            model, iter = selection.get_selected()
            self.swap_row(iter, 1)

    def swap_row(self, iter1, direction):
        try:
            path1 = self.path_by_iter(iter1)
            path2 = path1 + direction
            if path2 >= 0:
                iter2 = self.store.get_iter(path2)
                if path2 >= 0 and path2 < len(self.store):
                    self.store.swap(iter1, iter2)
        except:
            pass

class DBTree(gtk.ScrolledWindow):
    def __init__(self, dataset, id_field, list_field, parent_field, parent_of_root_value, border_width = 6):
        gtk.ScrolledWindow.__init__(self)
        self.id_field = id_field
        self.list_field = list_field
        self.parent_field = parent_field
        self.parent_of_root_value = parent_of_root_value
        self.set_border_width(border_width)
        self.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.tree = gtk.TreeView()
        self.add(self.tree)
        self.dataset = dataset
        dataset.controls.append(self)
        self.tree.connect('row-activated', self.do_on_dblclicked)
        self.tree.connect('cursor-changed', self.do_on_cursor_changed)
        self.tree.connect("destroy", self.do_on_destroy)
        self.on_select = None

    def do_on_destroy(self, widget):
        self.dataset.controls.remove(self)

    def do_on_dblclicked(self, treeview, path, view_column):
        pass

    def do_on_cursor_changed(self, treeview):
        model, iter = self.tree.get_selection().get_selected()
        if iter:
            cur_id = model.get_value(iter, 0)
            if self.on_select:
                self.on_select(cur_id)

    def update_field(self, field):
        pass

    def update(self, state):
        pass

    def create_column(self, field, index):
        cell = gtk.CellRendererText()
        cell.set_property('xalign', field.xalign())
        column = gtk.TreeViewColumn(field.field_name, cell, markup = index)
        column.set_widget(gtk.Label())
        column.get_widget().set_markup(u'<small><b>' + field.field_caption + '</b></small>')
        column.set_alignment(0.5)
        column.get_widget().show()
        column.set_resizable(True)
        column.set_expand(field.expand)
        self.tree.append_column(column)
        return column

    def fill_store(self, parent_iter, parent_value):
        for d in self.dataset:
            if d.field_by_name(self.parent_field).value == parent_value:
                iter = self.store.append(parent_iter, [d.field_by_name(self.id_field).value, d.field_by_name(self.list_field).value])
                rec_no = d.rec_no
                self.fill_store(iter, d.field_by_name(self.id_field).value)
                d.rec_no = rec_no

    def refresh(self):
        columns = self.tree.get_columns()
        for column in columns:
            self.tree.remove_column(column)

        column = self.create_column(self.dataset.field_by_name(self.id_field), 0)
        column.set_visible(False)
        column = self.create_column(self.dataset.field_by_name(self.list_field), 1)

        self.tree.set_headers_visible(False)
        self.tree.set_enable_search(False)
        self.tree.set_enable_tree_lines(False)

        self.store = gtk.TreeStore(int, str)
        self.fill_store(None, self.parent_of_root_value)
        self.tree.set_model(self.store)

    def expand_all(self):
        self.tree.expand_all()

    def expand_to_path(self, path):
        self.tree.expand_to_path(path)

    def expand_row(self, path, open_all=False):
        self.tree.expand_row(path, open_all)

    def collapse_row(self, path):
        self.tree.collapse_row(path)

    def expand_root(self):
        model = self.tree.get_model()
        iter = model.get_iter_root()
        self.tree.expand_row(model.get_path(iter), False)

    def get_path_by_id(self, id_value):

        def find_path(parent, model, id_value):
            node_iter = model.iter_children(parent)
            while node_iter:
                if model.get(node_iter, 0)[0] == id_value:
                    return model.get_path(node_iter)
                result = find_path(node_iter, model, id_value)
                if result:
                    return result
                node_iter = model.iter_next(node_iter)

        model = self.tree.get_model()
        return find_path(None, model, id_value)

class Popup(object):
    def __init__(self, field, entry, stretch = None, search=None):
        self.field = field
        self.search = search
        self.entry = entry
        parent_win = get_widget_window(entry)
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("key-press-event", self.popup_keypressed)
        self.window.set_border_width(5)
        win_pos = parent_win.get_position()
        self.widget = self.create_widget()
        self.window.add(self.widget)
        self.window.set_modal(True)
        self.window.set_transient_for(parent_win)
        self.window.set_title(self.get_title())
        rect = self.entry.get_allocation()
        if stretch:
            self.window.set_default_size(int(rect.width), int(rect.width))
        win_rect = self.window.get_allocation()
        win_width = win_rect.width
        win_height = win_rect.height
        screen_width = gtk.gdk.screen_width()
        screen_height = gtk.gdk.screen_height()
        left = win_pos[0] + rect.x
        top = win_pos[1] + rect.y + 2 * rect.height
        if top + win_height + rect.height > screen_height:
            top = top - win_height - 2 * rect.height
        self.window.move(left, top)
        self.window.show_all()

    def get_title(self):
        return ''

    def create_widget(self):
        pass

    def popup_keypressed(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.window.destroy()

class Calendar(Popup):
    def create_widget(self):
        self.calendar = gtk.Calendar()
        self.calendar.set_property("show-heading", True)
        self.calendar.set_property("show-day-names", True)
        self.calendar.connect("key-press-event", self.entry_keypressed)
        self.calendar.connect("day_selected_double_click", self.date_selected)
        return self.calendar

    def entry_keypressed(self, widget, event):
        print self.__dict__, self.calendar,
        if event.keyval == gtk.keysyms.Return:
            self.date_selected()

    def date_selected(self, widget = None):
        date = self.calendar.get_date()
        year, month, day = date
        if self.field.data_type == common.DATE:
            self.field.value = datetime.date(year, month+1, day)
        elif self.field.data_type == common.DATETIME:
            self.field.value = datetime.datetime(year, month+1, day)
        self.calendar = None
        self.window.destroy()

    def get_title(self):
        return 'Календарь'


class RefPopup(Popup):
    def create_widget(self):
        self.item = self.field.lookup_item.copy(details=False)
        self.item.details_active = False
        self.item.is_lookup_item = True
        self.item.lookup_field = self.field
        object_field = self.field.lookup_field
        self.fields = ['id', object_field]
        default_field = self.item.find_default_field()
        if self.field.owner and self.field.owner.on_param_lookup_item_show:
            self.field.owner.on_param_lookup_item_show(self.field, self.item)
        if self.field.owner and self.field.owner.on_field_lookup_item_show:
            self.field.owner.on_field_lookup_item_show(self.field, self.item)
        if self.field.filter and self.field.filter.owner.on_filter_lookup_item_show:
            self.field.filter.owner.on_filter_lookup_item_show(self.field.filter, self.item);
        if self.search and default_field:
            self.item.search(default_field.field_name, self.search)
        else:
            self.item.open()
        vbox = gtk.VBox(False, 4)
        self.tree_view = DBGrid(self.item, self.fields, border_width = 0)
        self.item.grid = self.tree_view
        vbox.pack_start(self.tree_view, True, True, 0)
        self.tree_view.grid.set_headers_visible(False)
        return vbox

    def get_title(self):
        return self.item.item_caption

class Chart(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect("expose_event", self.expose)

    def create_chart(self, surface):
        pass

    def repaint(self):
        self.queue_draw()

    def expose(self, widget, event):
        context = widget.window.cairo_create()
        surface = context.get_target()
        plot = self.create_chart(surface)
        if plot:
            plot.render()
        return False

class BarChart(Chart):
    def __init__(self,
                 data = None,
                 background = None,
                 border = 0,
                 grid = False,
                 rounded_corners = False,
                 three_dimension = False,
                 h_labels = None,
                 v_labels = None,
                 h_bounds = None,
                 v_bounds = None,
                 colors = None):
        self.data = data
        self.background = background
        self.border = border
        self.grid = grid
        self.rounded_corners = rounded_corners
        self.three_dimension = three_dimension
        self.h_labels = h_labels
        self.v_labels = v_labels
        self.h_bounds = h_bounds
        self.v_bounds = v_bounds
        self.colors = colors
        Chart.__init__(self)

    def create_chart(self, surface):
        alloc = self.get_allocation()
        if self.data:
            return CairoPlot.BarPlot(surface, self.data, alloc.width,
                alloc.height, self.background, self.border, self.grid,
                self.rounded_corners, self.three_dimension, self.h_labels,
                self.v_labels, self.h_bounds, self.v_bounds, self.colors)

class PieChart(Chart):
    def __init__(self,
        data=None,
        background=None,
        gradient=False,
        shadow=False,
        colors=None):

        self.data = data
        self.background = background
        self.gradient = gradient
        self.shadow = shadow
        self.colors = colors
        Chart.__init__(self)

    def create_chart(self, surface):
        alloc = self.get_allocation()
        if self.data:
            return CairoPlot.PiePlot(surface, self.data, alloc.width,
                alloc.height, self.background, self.gradient, self.shadow, self.colors)

class DonutChart(Chart):
    def __init__(self,
        data=None,
        background=None,
        gradient=False,
        shadow=False,
        colors=None,
        inner_radius=-1):

        self.data = data
        self.background = background
        self.gradient = gradient
        self.shadow = shadow
        self.colors = colors
        self.inner_radius = inner_radius
        Chart.__init__(self)

    def create_chart(self, surface):
        alloc = self.get_allocation()
        if self.data:
            return CairoPlot.DonutPlot(surface, self.data, alloc.width,
                alloc.height, self.background, self.gradient, self.shadow, self.colors, self.inner_radius)

def select_language():
    dialog = gtk.Dialog("", None, 0, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
        gtk.STOCK_OK, gtk.RESPONSE_OK))

    dialog.set_default_response(gtk.RESPONSE_OK)

    hbox = gtk.HBox(False, 8)
    hbox.set_border_width(8)
    dialog.vbox.pack_start(hbox, False, False, 0)

    table = gtk.Table(2, 1)
    table.set_row_spacings(6)
    table.set_col_spacings(6)
    hbox.pack_start(table, True, True, 0)

    label = gtk.Label(u'Select language')
    label.set_use_underline(True)
    table.attach(label, 0, 1, 0, 1)
    combobox = gtk.combo_box_entry_new_text()
    for lang in LANGUAGE:
        combobox.append_text(lang)
    combobox.set_active(0)
    dialog.grab_focus()
    table.attach(combobox, 1, 2, 0, 1)

    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
    if response == gtk.RESPONSE_OK:
        return combobox.get_active() + 1

def error_dialog(message):
    dialog = gtk.Dialog(u'', None, 0,
                        (gtk.STOCK_OK, gtk.RESPONSE_OK))

    dialog.props.has_separator = False

    hbox = gtk.HBox(False, 8)
    hbox.set_border_width(8)
    dialog.vbox.pack_start(hbox, False, False, 0)

    stock = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, #gtk.STOCK_DIALOG_AUTHENTICATION,
                                     gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(stock, False, False, 0)
    label = gtk.Label(message)
    hbox.pack_start(label, True, True, 0)
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

def select_from_list(select_list, caption=''):
    list_def = [{'caption': '', 'type': int},
        {'caption': 'Name', 'type': str},
        ]
    tasks_list = []
    for i, item in enumerate(select_list):
        tasks_list.append([i, item])
    result = None
    dialog = gtk.Dialog(caption, None, 0, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    grid = ListGrid(list_def, tasks_list)
    grid.set_size_request(300, 500)
    dialog.vbox.pack_start(grid)
    dialog.vbox.show_all()
    dialog.show_all()
    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        index = grid.selected_index()
        result = index
    dialog.destroy()
    return result


def login():
    login = None
    password = None

    dialog = gtk.Dialog(u'Registration', None, 0,
                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         gtk.STOCK_OK, gtk.RESPONSE_OK))

    dialog.props.has_separator = False
    dialog.set_default_response(gtk.RESPONSE_OK)

    hbox = gtk.HBox(False, 8)
    hbox.set_border_width(8)
    dialog.vbox.pack_start(hbox, False, False, 0)

    stock = gtk.image_new_from_stock(gtk.STOCK_DIALOG_AUTHENTICATION,
                                     gtk.ICON_SIZE_DIALOG)
    hbox.pack_start(stock, False, False, 0)

    table = gtk.Table(2, 2)
    table.set_row_spacings(4)
    table.set_col_spacings(4)
    hbox.pack_start(table, True, True, 0)

    label = gtk.Label(u'_Login')
    label.set_use_underline(True)
    table.attach(label, 0, 1, 0, 1)
    local_entry1 = gtk.Entry()
    local_entry1.set_activates_default(True)
    if login is not None:
        local_entry1.set_text(login)
    table.attach(local_entry1, 1, 2, 0, 1)
    label.set_mnemonic_widget(local_entry1)

    label = gtk.Label('_Password')
    label.set_use_underline(True)
    table.attach(label, 0, 1, 1, 2)
    local_entry2 = gtk.Entry()
    local_entry2.set_visibility(False)
    local_entry2.set_activates_default(True)
    if password is not None:
        local_entry2.set_text(password)
    table.attach(local_entry2, 1, 2, 1, 2)
    label.set_mnemonic_widget(local_entry2)

    dialog.show_all()
    while True:
        response = dialog.run()
        if response == gtk.RESPONSE_OK:
            login = local_entry1.get_text()
            password = local_entry2.get_text()
            if not login or not password:
                continue
            dialog.destroy()
            return login, password
        else:
            raise SystemExit

def get_widget_window(widget):
    if widget:
        if isinstance(widget, gtk.Window):
            return widget
        else:
            parent = widget.get_parent()
            while parent:
                if isinstance(parent, gtk.Window):
                    return parent
                else:
                    parent = parent.get_parent()
                    if not parent:
                        return None

YES = gtk.RESPONSE_YES
NO = gtk.RESPONSE_NO
CANCEL = gtk.RESPONSE_CANCEL

def question(parent, message):
    md = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, message)
    result = md.run()
    md.destroy()
    return result

def warning(parent, message):
    md = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, message)
    md.run()
    md.destroy()

def error(parent, message):
    md = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, message)
    md.run()
    md.destroy()

def yes_no_cancel(parent, message):
    md = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_NONE, message)
    md.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    md.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_NO)
    md.add_buttons(gtk.STOCK_YES, gtk.RESPONSE_YES)
    result = md.run()
    md.destroy()
    return result

def update_window_size(window):
    screen_width = gtk.gdk.screen_width()
    screen_height = gtk.gdk.screen_height()
    width, height = window.get_default_size()
    if width > screen_width:
        width = screen_width
    if height > screen_height:
        height = screen_height
    if os.name == 'nt':
        print height, screen_height
        if height > screen_height - 80:
            height = screen_height - 80
            window.set_default_size(width, height)
            window.move(int((screen_width - width) / 2), 0)
        else:
            window.set_default_size(width, height)
    else:
        window.set_default_size(width, height)

class RunTimeDialog():
    def __init__(self, widget, title, #right_buttons = None, left_buttons = None,
        width=600, height=400, modal=True, pos_center=True, maximize=False):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(title)

        if widget and modal:
            self.window.set_transient_for(get_widget_window(widget))
            self.window.set_modal(True)
        if pos_center:
            self.window.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        if maximize:
            self.window.maximize()

        self.window.set_default_size(width, height)
        update_window_size(self.window)
        #~ screen_width = gtk.gdk.screen_width()
        #~ screen_height = gtk.gdk.screen_height()
        #~ if width > screen_width:
            #~ width = screen_width
        #~ if height > screen_height:
            #~ height = screen_height
        #~ if os.name == 'nt':
            #~ print height, screen_height
            #~ if height > screen_height - 80:
                #~ height = screen_height - 80
                #~ self.window.set_default_size(width, height)
                #~ self.window.move(int((screen_width - width) / 2), 0)
            #~ else:
                #~ self.window.set_default_size(width, height)
        #~ else:
            #~ self.window.set_default_size(width, height)

        self.body = gtk.VBox(False, 6)
        self.buttons = {}

        hseparator = gtk.HSeparator()
        self.body.pack_end(hseparator, False, False)

        self.btns_box = gtk.HBox(False, 0)
        self.body.pack_end(self.btns_box, False, True, 0)
        self.window.add(self.body)

    def add_button(self, caption, handler, on_left=False, button_width=None):
        button = gtk.Button(caption)
        button.connect('clicked', handler)
        if button_width:
            button.set_size_request(button_width, -1)
        if on_left:
            self.btns_box.pack_start(button, False)
        else:
            self.btns_box.pack_end(button, False)
        return button

    def btn_item(self, btn, index):
        result = ''
        if len(btn) > index:
            return btn[index]

    def show(self):
        self.body.show_all()
        self.window.show()

    def close(self):
        self.window.destroy()

def file_browse(title='', open_action=True, file_name='', filters=None):
    result = None
    if open_action:
        dialog_action = gtk.FILE_CHOOSER_ACTION_OPEN
        dialog_buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OPEN, gtk.RESPONSE_OK)
    else:
        dialog_action = gtk.FILE_CHOOSER_ACTION_SAVE
        dialog_buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_SAVE, gtk.RESPONSE_OK)

    dialog = gtk.FileChooserDialog(title, action=dialog_action,
        buttons=dialog_buttons)

    dialog.set_default_response(gtk.RESPONSE_OK)
    if file_name:
        dialog.set_current_name(file_name)

    if not filters:
        filter = gtk.FileFilter()
        filter.set_name("Все файлы")
        filter.add_pattern("*")
        dialog.add_filter(filter)

    response = dialog.run()
    if response == gtk.RESPONSE_OK:
        result = dialog.get_filename()
    #~ elif response == gtk.RESPONSE_CANCEL:
        #~ result = None
    dialog.destroy()
    return result

def save_file(file_name=None, filters=None):
    return file_browse('Save', False, file_name, filters)

def open_file(filters=None):
    return file_browse('Open', filters=filters)

def key_name(key_val):
    return gtk.gdk.keyval_name(key_val)

def key_pressed(event):
    kp_dict = {'KP_Equal': '=', 'KP_Multiply': '*', 'KP_Add': '+',
        'KP_Separator': common.SETTINGS['DECIMAL_POINT'], 'KP_Subtract': '-', 'KP_Decimal': '.', 'KP_Divide': '/'}
    key = key_name(event.keyval)
    if not (event.state & gtk.gdk.CONTROL_MASK or event.state & gtk.gdk.MOD1_MASK):
        if not (event.keyval >= 0xF000 and key.find('KP_') == -1):
            if event.keyval == gtk.keysyms.comma:
                return '.'
            elif event.keyval == gtk.keysyms.period:
                return ','
            elif event.keyval == gtk.keysyms.plus:
                return '+'
            elif event.keyval == gtk.keysyms.minus:
                return '-'
            elif key.find('KP_') == 0:
                kp_val = key.replace('KP_', '')
                if kp_val.isdigit():
                    return kp_val
                else:
                    if kp_dict.get(key):
                        return kp_dict[key]
            else:
                return key

