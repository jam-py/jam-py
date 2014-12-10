#!/usr/bin/env python
# -*- coding: utf-8 -*-

# CairoPlot.py
#
# Copyright (c) 2008 Rodrigo Moreira Araújo
#
# Author: Rodrigo Moreiro Araujo <alf.rodrigo@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

#Contributor: João S. O. Bueno

__version__ = 1.1

import cairo
import math
import random

HORZ = 0
VERT = 1

def other_direction(direction):
    "explicit is better than implicit"
    if direction == HORZ:
        return VERT
    else:
        return HORZ

class Plot(object):
    def __init__(self, 
                 surface=None,
                 data=None,
                 width=640,
                 height=480,
                 background=None,
                 border = 0,
                 h_labels = None,
                 v_labels = None,
                 series_colors = None):
        self.create_surface(surface, width, height)
        self.width = width
        self.height = height
        self.context = cairo.Context(self.surface)
        self.load_series(data, h_labels, v_labels, series_colors)

        self.labels={}
        self.labels[HORZ] = h_labels
        self.labels[VERT] = v_labels

        self.font_size = 10
        
        self.set_background (background)
        self.border = border
        self.borders = {}
        
        self.line_color = (0.5, 0.5, 0.5)
        self.line_width = 0.5
        self.label_color = (0.0, 0.0, 0.0)
        self.grid_color = (0.8, 0.8, 0.8)
        
    
    def create_surface(self, surface, width=None, height=None):
        self.filename = None
        if isinstance(surface, cairo.Surface):
            self.surface = surface
            return
        if not type(surface) in (str, unicode): 
            raise TypeError("Surface should be either a Cairo surface or a filename, not %s" % surface)
        sufix = surface.rsplit(".")[-1].lower()
        self.filename = surface
        if sufix == "png":
            self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        elif sufix == "ps":
            self.surface = cairo.PSSurface(surface, width, height)
        elif sufix == "pdf":
            self.surface = cairo.PSSurface(surface, width, height)
        else:
            if sufix != "svg":
                self.filename += ".svg"
            self.surface = cairo.SVGSurface(self.filename, width, height)
    
    #def __del__(self):
    #    self.commit()

    def commit(self):
        try:
            self.context.show_page()
            if self.filename.endswith(".png"):
                self.surface.write_to_png(self.filename)
            else:
                self.surface.finish()
        except cairo.Error:
            pass
        
    def load_series (self, data, h_labels=None, v_labels=None, series_colors=None):
        #FIXME: implement Series class for holding series data,
        # labels and presentation properties
        
        #data can be a list, a list of lists or a dictionary with 
        #each item as a labeled data series.
        #we should (for teh time being) create a list of lists
        #and set labels for teh series rom  teh values provided.
        
        self.series_labels = []
        self.data = []
        #if we have labeled series:
        if hasattr(data, "keys"):
            #dictionary:
            self.series_labels = data.keys()
            for key in self.series_labels:
                self.data.append(data[key])
        #if we have a series of series:
        #changed the following line to adapt the Plot class to work
        #with GanttChart class
        #elif hasattr(data[0], "__getitem__"):
        elif max([hasattr(item,'__delitem__') for item in data]) :
            self.data = data
            self.series_labels = range(len(data))
        else:
            self.data = [data]
            self.series_labels = None
        #FIXME: select some pre-sets and allow these to be parametrized:
        random.seed(3)
        self.series_colors = series_colors
        if not self.series_colors:
            self.series_colors = [[random.random() for i in range(3)]  for series in self.data]
        self.series_widths = [1.0 for series in self.data]

    def get_width(self):
        return self.surface.get_width()
    def get_height(self):
        return self.surface.get_height()

    def set_background(self, background):
        if background is None:
            self.background = cairo.LinearGradient(self.width / 2, 0, self.width / 2, self.height)
            self.background.add_color_stop_rgb(0,1.0,1.0,1.0)
            self.background.add_color_stop_rgb(1.0,0.9,0.9,0.9)
        else:
            if type(background) in (cairo.LinearGradient, tuple):
                self.background = background
            else:
                raise TypeError ("Background should be either cairo.LinearGradient or a 3-tuple, not %s" % type(background))
        
    def render_background(self):
        if isinstance (self.background, cairo.LinearGradient):
            self.context.set_source(self.background)
        else:
            self.context.set_source_rgb(*self.background)
        self.context.rectangle(0,0, self.width, self.height)
        self.context.fill()
        
    def render_bounding_box(self):
        self.context.set_source_rgb(*self.line_color)
        self.context.set_line_width(self.line_width)
        self.context.rectangle(self.border, self.border,
                               self.width - 2 * self.border,
                               self.height - 2 * self.border)
        #CORRECTION: Added the next line so it will draw the outline of the bounding box
        self.context.stroke()

    def render(self):
        pass

class DotLinePlot(Plot):
    def __init__(self, 
                 surface=None,
                 data=None,
                 width=640,
                 height=480,
                 background=None,
                 border=0, 
                 axis = False,
                 grid = False,
                 dots = False,
                 h_labels = None,
                 v_labels = None,
                 h_bounds = None,
                 v_bounds = None):
        
        self.bounds = {}
        self.bounds[HORZ] = h_bounds
        self.bounds[VERT] = v_bounds
        
        Plot.__init__(self, surface, data, width, height, background, border, h_labels, v_labels)
        self.axis = axis
        self.grid = grid
        self.dots = dots

        self.max_value = {}
        
        self.h_label_angle = math.pi / 2.5

    def load_series(self, data, h_labels = None, v_labels = None, series_colors=None):
        Plot.load_series(self, data, h_labels, v_labels, series_colors)
        self.calc_boundaries()
    
    def calc_boundaries(self):
        if not self.bounds[HORZ]:
            self.bounds[HORZ] = (0, max([len(series) for series in (self.data)]))
            
        if not self.bounds[VERT]:
            max_data_value = min_data_value = 0
            for series in self.data:
                if max(series) > max_data_value:
                    max_data_value = max(series)
                if min(series) < min_data_value:
                    min_data_value = min(series)
            self.bounds[VERT] = (min_data_value, max_data_value)

    def calc_extents(self, direction):
        self.max_value[direction] = 0
        if self.labels[direction]:
            widest_word = max(self.labels[direction], key = lambda item: self.context.text_extents(item)[2])
            self.max_value[direction] = self.context.text_extents(widest_word)[2]
            self.borders[other_direction(direction)] = self.max_value[direction] + self.border
        else:
            self.max_value[direction] = self.context.text_extents(str(self.bounds[direction][1]))[2]
            self.borders[other_direction(direction)] = self.max_value[direction] + self.border + 20
            
    def calc_horz_extents(self):
        self.calc_extents(HORZ)
        
    def calc_vert_extents(self):
        self.calc_extents(VERT)
    
    def render_axis(self):
        cr = self.context
        h_border = self.borders[HORZ]
        v_border = self.borders[VERT]
        cr.set_source_rgb(*self.line_color)

        cr.move_to(h_border, self.height - v_border)
        cr.line_to(h_border, v_border)
        cr.stroke()

        cr.move_to(h_border, self.height - v_border)
        cr.line_to(self.width - h_border, self.height - v_border)
        cr.stroke()
    
    def render_labels(self):
        self.context.set_font_size(self.font_size * 0.8)
        
        self.render_horz_labels()
        self.render_vert_labels()
    
    def render_horz_labels(self):
        cr = self.context
        labels = self.labels[HORZ]
        if not labels:
            labels = [str(i) for i in range(self.bounds[HORZ][0], self.bounds[HORZ][1])]
        border = self.borders[HORZ]
        
        step = (self.width - 2 * border) / len(labels)
        x = border
        for item in labels:
            cr.set_source_rgb(*self.label_color)
            width = cr.text_extents(item)[2]
            cr.move_to(x, self.height - self.borders[VERT] + 10)
            cr.rotate(self.h_label_angle)
            cr.show_text(item)
            cr.rotate(-self.h_label_angle)
            #FIXME: render grid in a separate method
            if self.grid and x != border:
                cr.set_source_rgb(*self.grid_color)
                cr.move_to(x, self.height - self.borders[VERT])
                cr.line_to(x, self.borders[VERT])
                cr.stroke()
            x += step
    
    def render_vert_labels(self):
        cr = self.context
        labels = self.labels[VERT]
        if not labels:
            amplitude = self.bounds[VERT][1] - self.bounds[VERT][0]
            #if vertical labels need floating points
            if amplitude % 10:
                #label_type = lambda x : float(x)
                labels = ["%.2lf" % (float(self.bounds[VERT][0] + (amplitude * i / 10.0))) for i in range(10) ]
            else:
                #label_type = lambda x: int(x)
                labels = [str(int(self.bounds[VERT][0] + (amplitude * i / 10.0))) for i in range(10) ]
            #labels = [str(label_type(self.bounds[VERT][0] + (amplitude * i / 10.0))) for i in range(10) ]
        border = self.borders[VERT]
        
        step = (self.height - 2 * border)/ len(labels)
        y = self.height - border
        for item in labels:
            cr.set_source_rgb(*self.label_color)
            width = cr.text_extents(item)[2]
            cr.move_to(self.borders[HORZ] - width - 5,y)
            cr.show_text(item)
            #FIXME: render grid in a separate method
            if self.grid and y != self.height - border:
                cr.set_source_rgb(*self.grid_color)
                cr.move_to(self.borders[HORZ], y)
                cr.line_to(self.width - self.borders[HORZ], y)
                cr.stroke()
            y -=step
    
    
    def render(self):
        self.calc_horz_extents()
        self.calc_vert_extents()
            
        self.render_background()
        self.render_bounding_box()
        
        if self.axis:
            self.render_axis()

        self.render_labels()
        
        self.render_plot()
        
    def render_series_labels(self):
        #FIXME: implement this
        for key in self.series_labels:
            pass
            #This was not working in Rodrigo's original code anyway 

    def render_plot(self):
        #render_series_labels
        largest_series_length = len(max(self.data, key=len))
        #FIXME: plot_width and plot_height should be object properties and be re-used.
        plot_width = self.width - 2* self.borders[HORZ]
        plot_height = self.height - 2 * self.borders[VERT]
        plot_top = self.height - self.borders[VERT]
        
        series_amplitude = self.bounds[VERT][1] - self.bounds[VERT][0]
        
        horizontal_step = float (plot_width) / largest_series_length
        vertical_step = float (plot_height) / series_amplitude
        last = None
        cr = self.context
        for number, series in  enumerate (self.data):
            cr.set_source_rgb(*self.series_colors[number])
            x = self.borders[HORZ]
            last = None
            #FIXME: separate plotting of lines, dots and area

            for value in series:
                if last != None:
                    cr.move_to(x - horizontal_step, plot_top - int((last - self.bounds[VERT][0]) * vertical_step))
                    cr.line_to(x, plot_top - int((value - self.bounds[VERT][0])* vertical_step))
                    cr.set_line_width(self.series_widths[number])
                    cr.stroke()
                if self.dots:
                    cr.new_path()
                    cr.arc(x, plot_top - int((value - self.bounds[VERT][0]) * vertical_step), 3, 0, 2.1 * math.pi)
                    cr.close_path()
                    cr.fill()
                x += horizontal_step
                last = value

class FunctionPlot(DotLinePlot):
    def __init__(self, 
                 surface=None,
                 data=None,
                 width=640,
                 height=480,
                 background=None,
                 border=0, 
                 axis = False,
                 grid = False,
                 dots = False,
                 h_labels = None,
                 v_labels = None,
                 h_bounds = None,
                 v_bounds = None,
                 step = 1,
                 discrete = False):

        self.function = data
        self.step = step
        self.discrete = discrete
        data = []
        if h_bounds:
            i = h_bounds[0]
            while i < h_bounds[1]:
                data.append(self.function(i))
                i += self.step
        else:
            i = 0
            while i < 10:
                data.append(self.function(i))
                i += self.step

        DotLinePlot.__init__(self, surface, data, width, height, background, border, 
                             axis, grid, dots, h_labels, v_labels, h_bounds, v_bounds)
    
    def render_horz_labels(self):
        cr = self.context
        labels = self.labels[HORZ]
        if not labels:
            labels = []
            i = self.bounds[HORZ][0]
            while i<self.bounds[HORZ][1]:
                labels.append(str(i*self.step))
                i += (self.bounds[HORZ][1] - self.bounds[HORZ][0])/10
            #labels = [str(i*self.step) for i in range(self.bounds[HORZ][0], self.bounds[HORZ][1])]
        border = self.borders[HORZ]
        
        step = (self.width - 2 * border) / len(labels)
        x = border
        for item in labels:
            cr.set_source_rgb(*self.label_color)
            width = cr.text_extents(item)[2]
            cr.move_to(x, self.height - self.borders[VERT] + 10)
            cr.rotate(self.h_label_angle)
            cr.show_text(item)
            cr.rotate(-self.h_label_angle)
            #FIXME: render grid in a separate method
            if self.grid and x != border:
                cr.set_source_rgb(*self.grid_color)
                cr.move_to(x, self.height - self.borders[VERT])
                cr.line_to(x, self.borders[VERT])
                cr.stroke()
            x += step

    def render_plot(self):
        if not self.discrete:
            DotLinePlot.render_plot(self)
        else:
            #render_series_labels
            largest_series_length = len(max(self.data, key=len))
            #FIXME: plot_width and plot_height should be object properties and be re-used.
            plot_width = self.width - 2* self.borders[HORZ]
            plot_height = self.height - 2 * self.borders[VERT]
            plot_top = self.height - self.borders[VERT]

            series_amplitude = self.bounds[VERT][1] - self.bounds[VERT][0]

            horizontal_step = float (plot_width) / largest_series_length
            vertical_step = float (plot_height) / series_amplitude
            last = None
            cr = self.context
            for number, series in  enumerate (self.data):
                cr.set_source_rgb(*self.series_colors[number])
                x = self.borders[HORZ]
                for value in series:
                    cr.move_to(x, plot_top - int((value - self.bounds[VERT][0]) * vertical_step))
                    cr.line_to(x, plot_top)
                    cr.set_line_width(self.series_widths[number])
                    cr.stroke()
                    if self.dots:
                        cr.new_path()
                        cr.arc(x, plot_top - int((value - self.bounds[VERT][0]) * vertical_step), 3, 0, 2.1 * math.pi)
                        cr.close_path()
                        cr.fill()
                    x += horizontal_step




class BarPlot(Plot):
    def __init__(self, 
                 surface = None,
                 data = None,
                 width = 640,
                 height = 480,
                 background = None,
                 border = 0,
                 grid = False,
                 rounded_corners = False,
                 three_dimension = False,
                 h_labels = None,
                 v_labels = None,
                 h_bounds = None,
                 v_bounds = None,
                 series_colors = None):

        self.bounds = {}
        self.bounds[HORZ] = h_bounds
        self.bounds[VERT] = v_bounds

        Plot.__init__(self, surface, data, width, height, background, border, h_labels, v_labels, series_colors)
        self.grid = grid
        self.rounded_corners = rounded_corners
        self.three_dimension = three_dimension

        self.max_value = {}

    def load_series(self, data, h_labels = None, v_labels = None, series_colors = None):
        Plot.load_series(self, data, h_labels, v_labels, series_colors)
        if not series_colors:
            if hasattr( max(self.data, key = len), '__getitem__'):
                self.series_colors = [[random.random() for i in range(3)]  for item in max(self.data, key = len)]
            else:
                self.series_colors = [[random.random() for i in range(3)]  for series in self.data]
        self.calc_boundaries()

    def calc_boundaries(self):
        
        if not self.bounds[HORZ]:
            self.bounds[HORZ] = (0, len(self.data))

        if not self.bounds[VERT]:
            max_data_value = min_data_value = 0
            for series in self.data:
                if max(series) > max_data_value:
                    max_data_value = max(series)
                if min(series) < min_data_value:
                    min_data_value = min(series)
            self.bounds[VERT] = (min_data_value, max_data_value)

    def calc_extents(self, direction):
        self.max_value[direction] = 0
        if self.labels[direction]:
            widest_word = max(self.labels[direction], key = lambda item: self.context.text_extents(item)[2])
            self.max_value[direction] = self.context.text_extents(widest_word)[3 - direction]
            self.borders[other_direction(direction)] = (2-direction)*self.max_value[direction] + self.border + direction*(5)
        else:
            self.borders[other_direction(direction)] = self.border

    def calc_horz_extents(self):
        self.calc_extents(HORZ)

    def calc_vert_extents(self):
        self.calc_extents(VERT)
        if self.labels[VERT] and not self.labels[HORZ]:
            self.borders[VERT] += 10

    def render(self):
        self.calc_horz_extents()
        self.calc_vert_extents()
        
        self.render_background()
        self.render_bounding_box()
        
        if self.grid:
            self.render_grid()
        if self.three_dimension:
            self.render_ground()

        self.render_labels()

        self.render_plot()
    
    def draw_3d_rectangle_front(self, x0, y0, x1, y1, shift):
        self.context.rectangle(x0-shift, y0+shift, x1-x0, y1-y0)
    def draw_3d_rectangle_side(self, x0, y0, x1, y1, shift):
        self.context.move_to(x1-shift,y0+shift)
        self.context.line_to(x1, y0)
        self.context.line_to(x1, y1)
        self.context.line_to(x1-shift, y1+shift)
        self.context.line_to(x1-shift, y0+shift)
        self.context.close_path()
    def draw_3d_rectangle_top(self, x0, y0, x1, y1, shift):
        self.context.move_to(x0-shift,y0+shift)
        self.context.line_to(x0, y0)
        self.context.line_to(x1, y0)
        self.context.line_to(x1-shift, y0+shift)
        self.context.line_to(x0-shift, y0+shift)
        self.context.close_path()

    def render_grid(self):
        self.context.set_source_rgb(0.8, 0.8, 0.8)
        if self.labels[VERT]:
            lines = len(self.labels[VERT])
        else:
            lines = 10
        vertical_step = float(self.height - 2*self.borders[VERT])/(lines-1)
        y = self.borders[VERT]
        for x in xrange(0, lines):
            self.context.move_to(self.borders[HORZ], y)
            self.context.line_to(self.width - self.border, y)
            self.context.stroke()
            y += vertical_step

    def render_ground(self):
        self.draw_3d_rectangle_front(self.borders[HORZ], self.height - self.borders[VERT], 
                                     self.width - self.borders[HORZ], self.height - self.borders[VERT] + 5, 10)
        self.context.fill()

        self.draw_3d_rectangle_side (self.borders[HORZ], self.height - self.borders[VERT], 
                                     self.width - self.borders[HORZ], self.height - self.borders[VERT] + 5, 10)
        self.context.fill()

        self.draw_3d_rectangle_top  (self.borders[HORZ], self.height - self.borders[VERT], 
                                     self.width - self.borders[HORZ], self.height - self.borders[VERT] + 5, 10)
        self.context.fill()

    def render_labels(self):
        self.context.set_font_size(self.font_size * 0.8)

        if self.labels[HORZ]:
            self.render_horz_labels()
        if self.labels[VERT]:
            self.render_vert_labels()

    def render_labels(self):
        self.context.set_font_size(self.font_size * 0.8)

        if self.labels[HORZ]:
            self.render_horz_labels()
        if self.labels[VERT]:
            self.render_vert_labels()

    def render_horz_labels(self):
        step = (self.width - self.borders[HORZ] - self.border)/len(self.labels[HORZ])
        x = self.borders[HORZ] + step/2

        for item in self.labels[HORZ]:
            self.context.set_source_rgb(*self.label_color)
            width = self.context.text_extents(item)[2]
            self.context.move_to(x - width/2, self.height - self.borders[VERT] + self.max_value[HORZ] + 3)
            self.context.show_text(item)
            x += step

    def render_vert_labels(self):
        y = self.borders[VERT]
        step = (self.height - 2*self.borders[VERT])/(len(self.labels[VERT]) - 1)

        self.labels[VERT].reverse()
        for item in self.labels[VERT]:
            self.context.set_source_rgb(*self.label_color)
            width, height = self.context.text_extents(item)[2:4]
            self.context.move_to(self.borders[HORZ] - width - 5, y + height/2)
            self.context.show_text(item)
            y += step
        self.labels[VERT].reverse()
        
    def draw_rectangle(self, x0, y0, x1, y1):
        self.context.arc(x0+5, y0+5, 5, -math.pi, -math.pi/2)
        self.context.line_to(x1-5, y0)
        self.context.arc(x1-5, y0+5, 5, -math.pi/2, 0)
        self.context.line_to(x1, y1-5)
        self.context.arc(x1-5, y1-5, 5, 0, math.pi/2)
        self.context.line_to(x0+5, y1)
        self.context.arc(x0+5, y1-5, 5, math.pi/2, math.pi)
        self.context.line_to(x0, y0+5)
        self.context.close_path()

    def render_plot(self):
        plot_width = self.width - self.borders[HORZ] - self.border
        plot_height = self.height - 2 * self.borders[VERT]
        plot_top = self.height - self.borders[VERT]

        series_amplitude = self.bounds[VERT][1] - self.bounds[VERT][0]

        y0 = self.borders[VERT]
        
        horizontal_step = float (plot_width) / len(self.data)
        vertical_step = float (plot_height) / series_amplitude

        for i,series in enumerate(self.data):
            inner_step = horizontal_step/(len(series) + 0.4)
            x0 = self.borders[HORZ] + i*horizontal_step + 0.2*inner_step
            for number,key in enumerate(series):
                linear = cairo.LinearGradient( x0, key*vertical_step/2, x0 + inner_step, key*vertical_step/2 )
                r,g,b = self.series_colors[number]
                linear.add_color_stop_rgb(0.0, 3.5*r/5.0, 3.5*g/5.0, 3.5*b/5.0)
                linear.add_color_stop_rgb(1.0, r, g, b)
                self.context.set_source(linear)
                
                if self.rounded_corners and key != 0:
                    self.draw_rectangle(x0, y0 + (series_amplitude - key)*vertical_step, x0+inner_step, y0 + series_amplitude*vertical_step)
                    self.context.fill()
                elif self.three_dimension:
                    self.draw_3d_rectangle_front(x0, y0 + (series_amplitude - key)*vertical_step, x0+inner_step, y0 + series_amplitude*vertical_step, 5)
                    self.context.fill()
                    self.draw_3d_rectangle_side(x0, y0 + (series_amplitude - key)*vertical_step, x0+inner_step, y0 + series_amplitude*vertical_step, 5)
                    self.context.fill()
                    self.draw_3d_rectangle_top(x0, y0 + (series_amplitude - key)*vertical_step, x0+inner_step, y0 + series_amplitude*vertical_step, 5)
                    self.context.fill()
                else:
                    self.context.rectangle(x0, y0 + (series_amplitude - key)*vertical_step, inner_step, key*vertical_step)
                    self.context.fill()
                
                x0 += inner_step

class PiePlot(Plot):
    def __init__ (self,
            surface=None, 
            data=None, 
            width=640, 
            height=480, 
            background=None,
            gradient=False,
            shadow=False,
            series_colors=None):

        Plot.__init__(self, surface, data, width, height, background, series_colors = series_colors)
        self.center = (self.width/2, self.height/2)
        self.total = sum(self.data)
        self.radius = min(self.width/3,self.height/3)
        self.gradient = gradient
        self.shadow = shadow

    def load_series(self, data, h_labels=None, v_labels=None, series_colors=None):
        Plot.load_series(self, data, series_colors = series_colors)

    def draw_piece(self, angle, next_angle):
        self.context.move_to(self.center[0],self.center[1])
        self.context.line_to(self.center[0] + self.radius*math.cos(angle), self.center[1] + self.radius*math.sin(angle))
        self.context.arc(self.center[0], self.center[1], self.radius, angle, next_angle)
        self.context.line_to(self.center[0], self.center[1])
        self.context.close_path()

    def render(self):
        self.render_background()
        self.render_bounding_box()
        if self.shadow:
            self.render_shadow()
        self.render_plot()
        self.render_series_labels()

    def render_shadow(self):
        horizontal_shift = 3
        vertical_shift = 3
        self.context.set_source_rgba(0, 0, 0, 0.5)
        self.context.arc(self.center[0] + horizontal_shift, self.center[1] + vertical_shift, self.radius, 0, 2*math.pi)
        self.context.fill()

    def render_series_labels(self):
        angle = 0
        next_angle = 0
        x0,y0 = self.center
        cr = self.context
        for number,key in enumerate(self.series_labels):
            next_angle = angle + 2.0*math.pi*self.data[number]/self.total
            cr.set_source_rgb(*self.series_colors[number])
            w = cr.text_extents(key)[2]
            if (angle + next_angle)/2 < math.pi/2 or (angle + next_angle)/2 > 3*math.pi/2:
                cr.move_to(x0 + (self.radius+10)*math.cos((angle+next_angle)/2), y0 + (self.radius+10)*math.sin((angle+next_angle)/2) )
            else:
                cr.move_to(x0 + (self.radius+10)*math.cos((angle+next_angle)/2) - w, y0 + (self.radius+10)*math.sin((angle+next_angle)/2) )
            cr.show_text(key)
            angle = next_angle

    def render_plot(self):
        angle = 0
        next_angle = 0
        x0,y0 = self.center
        cr = self.context
        for number,series in enumerate(self.data):
            next_angle = angle + 2.0*math.pi*series/self.total
            if self.gradient:        
                gradient_color = cairo.RadialGradient(self.center[0], self.center[1], 0, self.center[0], self.center[1], self.radius)
                gradient_color.add_color_stop_rgb(0.3, self.series_colors[number][0], 
                                                       self.series_colors[number][1], 
                                                       self.series_colors[number][2])
                gradient_color.add_color_stop_rgb(1, self.series_colors[number][0]*0.7,
                                                     self.series_colors[number][1]*0.7,
                                                     self.series_colors[number][2]*0.7)
                cr.set_source(gradient_color)
            else:
                cr.set_source_rgb(*self.series_colors[number])

            self.draw_piece(angle, next_angle)
            cr.fill()

            cr.set_source_rgb(1.0, 1.0, 1.0)
            self.draw_piece(angle, next_angle)
            cr.stroke()

            angle = next_angle

class DonutPlot(PiePlot):
    def __init__ (self,
            surface=None, 
            data=None, 
            width=640, 
            height=480,
            background=None,
            gradient=False,
            shadow=False,
            series_colors=None,
            inner_radius=-1):

        Plot.__init__(self, surface, data, width, height, background, series_colors = series_colors)
        self.center = (self.width/2, self.height/2)
        self.total = sum(self.data)
        self.radius = min(self.width/3,self.height/3)
        self.inner_radius = inner_radius*self.radius
        if inner_radius == -1:
            self.inner_radius = self.radius/3
        self.gradient = gradient
        self.shadow = shadow

    def draw_piece(self, angle, next_angle):
        self.context.move_to(self.center[0] + (self.inner_radius)*math.cos(angle), self.center[1] + (self.inner_radius)*math.sin(angle))
        self.context.line_to(self.center[0] + self.radius*math.cos(angle), self.center[1] + self.radius*math.sin(angle))
        self.context.arc(self.center[0], self.center[1], self.radius, angle, next_angle)
        self.context.line_to(self.center[0] + (self.inner_radius)*math.cos(next_angle), self.center[1] + (self.inner_radius)*math.sin(next_angle))
        self.context.arc_negative(self.center[0], self.center[1], self.inner_radius, next_angle, angle)
        self.context.close_path()
    
    def render_shadow(self):
        horizontal_shift = 3
        vertical_shift = 3
        self.context.set_source_rgba(0, 0, 0, 0.5)
        self.context.arc(self.center[0] + horizontal_shift, self.center[1] + vertical_shift, self.inner_radius, 0, 2*math.pi)
        self.context.arc_negative(self.center[0] + horizontal_shift, self.center[1] + vertical_shift, self.radius, 0, -2*math.pi)
        self.context.fill()

class GanttChart (Plot) :
    def __init__(self,
                 surface = None,
                 data = None,
                 width = 640,
                 height = 480,
                 h_labels = None,
                 v_labels = None,
                 colors = None):
        self.bounds = {}
        self.max_value = {}
        Plot.__init__(self, surface, data, width, height,  h_labels = h_labels, v_labels = v_labels, series_colors = colors)

    def load_series(self, data, h_labels=None, v_labels=None, series_colors=None):
        Plot.load_series(self, data, h_labels, v_labels, series_colors)
        self.calc_boundaries()

    def calc_boundaries(self):
        self.bounds[HORZ] = (0,len(self.data))
        for item in self.data:
            if hasattr(item, "__delitem__"):
                for sub_item in item:
                    end_pos = max(sub_item)
            else:
                end_pos = max(item)
        self.bounds[VERT] = (0,end_pos)

    def calc_extents(self, direction):
        self.max_value[direction] = 0
        if self.labels[direction]:
            widest_word = max(self.labels[direction], key = lambda item: self.context.text_extents(item)[2])
            self.max_value[direction] = self.context.text_extents(widest_word)[2]
        else:
            self.max_value[direction] = self.context.text_extents( str(self.bounds[direction][1] + 1) )[2]

    def calc_horz_extents(self):
        self.calc_extents(HORZ)
        self.borders[HORZ] = 100 + self.max_value[HORZ]

    def calc_vert_extents(self):
        self.calc_extents(VERT)
        self.borders[VERT] = self.height/(self.bounds[HORZ][1] + 1)

    def calc_steps(self):
        self.horizontal_step = (self.width - self.borders[HORZ])/(len(self.labels[VERT]))
        self.vertical_step = self.borders[VERT]

    def render(self):
        self.calc_horz_extents()
        self.calc_vert_extents()
        self.calc_steps()
        self.render_background()

        self.render_labels()
        self.render_grid()
        self.render_plot()

    def render_background(self):
        cr = self.context
        cr.set_source_rgb(255,255,255)
        cr.rectangle(0,0,self.width, self.height)
        cr.fill()
        for number,item in enumerate(self.data):
            linear = cairo.LinearGradient(self.width/2, self.borders[VERT] + number*self.vertical_step, 
                                          self.width/2, self.borders[VERT] + (number+1)*self.vertical_step)
            linear.add_color_stop_rgb(0,1.0,1.0,1.0)
            linear.add_color_stop_rgb(1.0,0.9,0.9,0.9)
            cr.set_source(linear)
            cr.rectangle(0,self.borders[VERT] + number*self.vertical_step,self.width,self.vertical_step)
            cr.fill()

    def render_grid(self):
        cr = self.context
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.set_dash((1,0,0,0,0,0,1))
        cr.set_line_width(0.5)
        for number,label in enumerate(self.labels[VERT]):
            h = cr.text_extents(label)[3]
            cr.move_to(self.borders[HORZ] + number*self.horizontal_step, self.vertical_step/2 + h)
            cr.line_to(self.borders[HORZ] + number*self.horizontal_step, self.height)
        cr.stroke()

    def render_labels(self):
        self.context.set_font_size(0.02 * self.width)

        self.render_horz_labels()
        self.render_vert_labels()

    def render_horz_labels(self):
        cr = self.context
        labels = self.labels[HORZ]
        if not labels:
            labels = [str(i) for i in range(1, self.bounds[HORZ][1] + 1)  ]
        for number,label in enumerate(labels):
            if label != None:
                cr.set_source_rgb(0.5, 0.5, 0.5)
                w,h = cr.text_extents(label)[2], cr.text_extents(label)[3]
                cr.move_to(40,self.borders[VERT] + number*self.vertical_step + self.vertical_step/2 + h/2)
                cr.show_text(label)
            
    def render_vert_labels(self):
        cr = self.context
        labels = self.labels[VERT]
        if not labels:
            labels = [str(i) for i in range(1, self.bounds[VERT][1] + 1)  ]
        for number,label in enumerate(labels):
            w,h = cr.text_extents(label)[2], cr.text_extents(label)[3]
            cr.move_to(self.borders[HORZ] + number*self.horizontal_step - w/2, self.vertical_step/2)
            cr.show_text(label)

    def render_rectangle(self, x0, y0, x1, y1, color):
        self.draw_shadow(x0, y0, x1, y1)
        self.draw_rectangle(x0, y0, x1, y1, color)

    def draw_rectangular_shadow(self, gradient, x0, y0, w, h):
        self.context.set_source(gradient)
        self.context.rectangle(x0,y0,w,h)
        self.context.fill()
    
    def draw_circular_shadow(self, x, y, radius, ang_start, ang_end, mult, shadow):
        gradient = cairo.RadialGradient(x, y, 0, x, y, 2*radius)
        gradient.add_color_stop_rgba(0, 0, 0, 0, shadow)
        gradient.add_color_stop_rgba(1, 0, 0, 0, 0)
        self.context.set_source(gradient)
        self.context.move_to(x,y)
        self.context.line_to(x + mult[0]*radius,y + mult[1]*radius)
        self.context.arc(x, y, 8, ang_start, ang_end)
        self.context.line_to(x,y)
        self.context.close_path()
        self.context.fill()

    def draw_rectangle(self, x0, y0, x1, y1, color):
        cr = self.context
        middle = (x0+x1)/2
        linear = cairo.LinearGradient(middle,y0,middle,y1)
        linear.add_color_stop_rgb(0,3.5*color[0]/5.0, 3.5*color[1]/5.0, 3.5*color[2]/5.0)
        linear.add_color_stop_rgb(1,color[0],color[1],color[2])
        cr.set_source(linear)

        cr.arc(x0+5, y0+5, 5, 0, 2*math.pi)
        cr.arc(x1-5, y0+5, 5, 0, 2*math.pi)
        cr.arc(x0+5, y1-5, 5, 0, 2*math.pi)
        cr.arc(x1-5, y1-5, 5, 0, 2*math.pi)
        cr.rectangle(x0+5,y0,x1-x0-10,y1-y0)
        cr.rectangle(x0,y0+5,x1-x0,y1-y0-10)
        cr.fill()

    def draw_shadow(self, x0, y0, x1, y1):
        shadow = 0.4
        h_mid = (x0+x1)/2
        v_mid = (y0+y1)/2
        h_linear_1 = cairo.LinearGradient(h_mid,y0-4,h_mid,y0+4)
        h_linear_2 = cairo.LinearGradient(h_mid,y1-4,h_mid,y1+4)
        v_linear_1 = cairo.LinearGradient(x0-4,v_mid,x0+4,v_mid)
        v_linear_2 = cairo.LinearGradient(x1-4,v_mid,x1+4,v_mid)

        h_linear_1.add_color_stop_rgba( 0, 0, 0, 0, 0)
        h_linear_1.add_color_stop_rgba( 1, 0, 0, 0, shadow)
        h_linear_2.add_color_stop_rgba( 0, 0, 0, 0, shadow)
        h_linear_2.add_color_stop_rgba( 1, 0, 0, 0, 0)
        v_linear_1.add_color_stop_rgba( 0, 0, 0, 0, 0)
        v_linear_1.add_color_stop_rgba( 1, 0, 0, 0, shadow)
        v_linear_2.add_color_stop_rgba( 0, 0, 0, 0, shadow)
        v_linear_2.add_color_stop_rgba( 1, 0, 0, 0, 0)

        self.draw_rectangular_shadow(h_linear_1,x0+4,y0-4,x1-x0-8,8)
        self.draw_rectangular_shadow(h_linear_2,x0+4,y1-4,x1-x0-8,8)
        self.draw_rectangular_shadow(v_linear_1,x0-4,y0+4,8,y1-y0-8)
        self.draw_rectangular_shadow(v_linear_2,x1-4,y0+4,8,y1-y0-8)

        self.draw_circular_shadow(x0+4, y0+4, 4, math.pi, 3*math.pi/2, (-1,0), shadow)
        self.draw_circular_shadow(x1-4, y0+4, 4, 3*math.pi/2, 2*math.pi, (0,-1), shadow)
        self.draw_circular_shadow(x0+4, y1-4, 4, math.pi/2, math.pi, (0,1), shadow)
        self.draw_circular_shadow(x1-4, y1-4, 4, 0, math.pi/2, (1,0), shadow)

    def render_plot(self):
        for number,item in enumerate(self.data):
            if hasattr(item, "__delitem__") :
                for space in item:
                    self.render_rectangle(self.borders[HORZ] + space[0]*self.horizontal_step, 
                                          self.borders[VERT] + number*self.vertical_step + self.vertical_step/4.0,
                                          self.borders[HORZ] + space[1]*self.horizontal_step, 
                                          self.borders[VERT] + number*self.vertical_step + 3.0*self.vertical_step/4.0, 
                                          self.series_colors[number])
            else:
                space = item
                self.render_rectangle(self.borders[HORZ] + space[0]*self.horizontal_step, 
                                      self.borders[VERT] + number*self.vertical_step + self.vertical_step/4.0,
                                      self.borders[HORZ] + space[1]*self.horizontal_step, 
                                      self.borders[VERT] + number*self.vertical_step + 3.0*self.vertical_step/4.0, 
                                      self.series_colors[number])
def dot_line_plot(name,
                  data,
                  width,
                  height,
                  background = None,
                  border = 0,
                  axis = False,
                  grid = False,
                  dots = False,
                  h_labels= None,
                  v_labels = None,
                  h_bounds = None,
                  v_bounds = None):
    '''
        - Function to plot graphics using dots and lines.
        
        dot_line_plot (name, data, width, height, background = None, border = 0, axis = False, grid = False, h_labels = None, v_labels = None, h_bounds = None, v_bounds = None)

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient. 
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        axis - Whether or not the axis are to be drawn;
        grid - Whether or not the gris is to be drawn;
        dots - Whether or not dots should be shown at each point;
        h_labels, v_labels - lists of strings containing the horizontal and vertical labels for the axis;
        h_bounds, v_bounds - tuples containing the lower and upper value bounds for the data to be plotted.

        - Examples of use

        teste_data = [0, 1, 3, 8, 9, 0, 10, 10, 2, 1]
        CairoPlot.dot_line_plot('teste', teste_data, 400, 300)
        
        teste_data_2 = {"john" : [10, 10, 10, 10, 30], "mary" : [0, 0, 3, 5, 15], "philip" : [13, 32, 11, 25, 2]}
        teste_h_labels = ["jan/2008", "feb/2008", "mar/2008", "apr/2008", "may/2008"]
        CairoPlot.dot_line_plot('teste2', teste_data_2, 400, 300, axis = True, grid = True, dots = True, h_labels = teste_h_labels)
    '''
    plot = DotLinePlot(name, data, width, height, background, border,
                       axis, grid, dots, h_labels, v_labels, h_bounds, v_bounds)
    plot.render()
    plot.commit()

def function_plot(name,
                  data,
                  width,
                  height,
                  background = None,
                  border = 0,
                  axis = True,
                  grid = False,
                  dots = False,
                  h_labels = None,
                  v_labels = None,
                  h_bounds = None,
                  v_bounds = None,
                  step = 1,
                  discrete = False):

    '''
        - Function to plot functions.
        
        function_plot(name, data, width, height, background = None, border = 0, axis = True, grid = False, dots = False, h_labels = None, v_labels = None, h_bounds = None, v_bounds = None, step = 1, discrete = False)

        - Parameters
        
        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient. 
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        axis - Whether or not the axis are to be drawn;
        grid - Whether or not the gris is to be drawn;
        dots - Whether or not dots should be shown at each point;
        h_labels, v_labels - lists of strings containing the horizontal and vertical labels for the axis;
        h_bounds, v_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        step - the horizontal distance from one point to the other. The smaller, the smoother the curve will be;
        discrete - whether or not the function should be plotted in discrete format.
       
        - Example of use

        data = lambda x : x**2
        CairoPlot.function_plot('function4', data, 400, 300, grid = True, h_bounds=(-10,10), step = 0.1)
        
    '''
   
    plot = FunctionPlot(name, data, width, height, background, border,
                        axis, grid, dots, h_labels, v_labels, h_bounds, v_bounds, step, discrete)
    plot.render()
    plot.commit()


def pie_plot(name, data, width, height, background = None, gradient = False, shadow = False, colors = None):

    '''
        - Function to plot pie graphics.

        pie_plot(name, data, width, height, background = None, gradient = False)

        - Parameters
        
        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient. 
                     If left None, a gray to white gradient will be generated;
        gradient - Whether or not the pie color will be painted with a gradient;
        shadow - Whether or not there will be a shadow behind the pie;
        colors - List of slices colors.

        - Examples of use
        
        teste_data = {"john" : 123, "mary" : 489, "philip" : 890 , "suzy" : 235}
        CairoPlot.pie_plot("pie_teste", teste_data, 500, 500)
        
    '''

    plot = PiePlot(name, data, width, height, background, gradient, shadow, series_colors = colors)
    plot.render()
    plot.commit()

def donut_plot(name, data, width, height, background = None, gradient = False, shadow = False, colors = None, inner_radius = -1):

    '''
        - Function to plot donut graphics.

        donut_plot(name, data, width, height, background = None, gradient = False, inner_radius = -1)

        - Parameters
        
        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient. 
                     If left None, a gray to white gradient will be generated;
        shadow - Whether or not there will be a shadow behind the donut;
        gradient - Whether or not the donut color will be painted with a gradient;
        colors - List of slices colors;
        inner_radius - The radius of the donut's inner circle.

        - Examples of use
        
        teste_data = {"john" : 123, "mary" : 489, "philip" : 890 , "suzy" : 235}
        CairoPlot.donut_plot("donut_teste", teste_data, 500, 500)
        
    '''

    plot = DonutPlot(name, data, width, height, background, gradient, shadow, colors, inner_radius)
    plot.render()
    plot.commit()

def gantt_chart(name, pieces, width, height, h_labels, v_labels, colors):

    '''
        - Function to generate Gantt Diagrams.

        gantt_chart(name, pieces, width, height, h_labels, v_labels, colors):

        - Parameters
        
        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        pieces - A list defining the spaces to be drawn. The user must pass, for each line, the index of its start and the index of its end. If a line must have two or more spaces, they must be passed inside a list;
        width, height - Dimensions of the output image;
        h_labels - A list of names for each of the vertical lines;
        v_labels - A list of names for each of the horizontal spaces;
        colors - List containing the colors expected for each of the horizontal spaces

        - Example of use

        pieces = [ (0.5,5.5) , [(0,4),(6,8)] , (5.5,7) , (7,8)]
        h_labels = [ 'teste01', 'teste02', 'teste03', 'teste04']
        v_labels = [ '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010' ]
        colors = [ (1.0, 0.0, 0.0), (1.0, 0.7, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0) ]
        CairoPlot.gantt_chart('gantt_teste', pieces, 600, 300, h_labels, v_labels, colors)
        
    '''

    plot = GanttChart(name, pieces, width, height, h_labels, v_labels, colors)
    plot.render()
    plot.commit()

def bar_plot(name, 
             data, 
             width, 
             height, 
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

    '''
        - Function to generate Bar Plot Charts.

        bar_plot(name, data, width, height, background, border, grid, rounded_corners, three_dimension, 
                 h_labels, v_labels, h_bounds, v_bounds, colors):

        - Parameters
        
        name - Name of the desired output file, no need to input the .svg as it will be added at runtime;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient. 
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        grid - Whether or not the gris is to be drawn;
        rounded_corners - Whether or not the bars should have rounded corners;
        three_dimension - Whether or not the bars should be drawn in pseudo 3D;
        h_labels, v_labels - lists of strings containing the horizontal and vertical labels for the axis;
        h_bounds, v_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        colors - List containing the colors expected for each of the bars.

        - Example of use

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        CairoPlot.bar_plot ('bar2', data, 400, 300, border = 20, grid = True, rounded_corners = False)
    '''

    plot = BarPlot(name, data, width, height, background, border,
                   grid, rounded_corners, three_dimension, h_labels, v_labels, h_bounds, v_bounds, colors)
    plot.render()
    plot.commit()

