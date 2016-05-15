! function($) {

    "use strict"; // jshint ;_;


    /* TYPEAHEAD PUBLIC CLASS DEFINITION
     * ================================= */

    var JamTypeahead = function(element, options) {
        this.$element = $(element)
        this.options = $.extend({}, $.fn.jamtypeahead.defaults, options)
        this.matcher = this.options.matcher || this.matcher
        this.sorter = this.options.sorter || this.sorter
        this.highlighter = this.options.highlighter || this.highlighter
        this.updater = this.options.updater || this.updater
        this.source = this.options.source
        this.$menu = $(this.options.menu)
        this.shown = false
        this.listen()
    }

    JamTypeahead.prototype = {

        constructor: JamTypeahead,

        select: function() {
            var $li = this.$menu.find('.active'),
                rec_no = $li.attr('rec-value');
            this.options.lookup_item.rec_no = rec_no;
            this.options.lookup_item.set_lookup_field_value();
            return this.hide();
        },

        updater: function(item) {
            return item
        },

        show: function() {
            var pos = $.extend({}, this.$element.position(), {
                height: this.$element[0].offsetHeight
            })

            this.$menu
                .insertAfter(this.$element)
                .css({
                    top: pos.top + pos.height,
                    left: pos.left,
                    "min-width": this.$element.innerWidth(),
                    "max-width": $(window).width() - this.$element.offset().left - 20,
                    "overflow": "hidden"
                })
                .show()

            this.shown = true
            return this
        },

        hide: function() {
            this.$menu.hide()
            this.shown = false
            return this
        },

        do_lookup: function(event) {
            var items
            this.query = this.$element.val()
            if (!this.query || this.query.length < this.options.minLength) {
                return this.shown ? this.hide() : this
            }
            items = $.isFunction(this.source) ? this.source(this.query, $.proxy(this.process, this)) : this.source
            return items ? this.process(items) : this
        },

        lookup: function(event) {
            var self = this;
            if (this.options.field && this.options.field.lookup_item) {
                clearTimeout(this.timeOut);
                this.timeOut = setTimeout(function() {
                        self.do_lookup(event);
                    },
                    400
                );
            } else {
                this.do_lookup(event);
            }
        },

        process: function(items) {
            var that = this

            items = $.grep(items, function(item) {
                return that.matcher(item)
            })

            items = this.sorter(items)

            if (!items.length) {
                return this.shown ? this.hide() : this
            }

            return this.render(items.slice(0, this.options.items)).show()
        },

        matcher: function(item) {
            return true
            return ~item.toLowerCase().indexOf(this.query.toLowerCase())
        },

        sorter: function(items) {
            return items
            //~ var beginswith = [],
                //~ caseSensitive = [],
                //~ caseInsensitive = [],
                //~ item,
                //~ id
//~
            //~ while (item = items.shift()) {
                //~ item = item[0],
                //~ id = item[1]
//~
                //~ if (!item.toLowerCase().indexOf(this.query.toLowerCase())) beginswith.push([item, id])
                //~ else if (~item.indexOf(this.query)) caseSensitive.push([item, id])
                //~ else caseInsensitive.push([item, id])
            //~ }
//~
            //~ return beginswith.concat(caseSensitive, caseInsensitive)
        },

        highlighter: function(item) {
            var i = 0,
                query,
                result = item,
                strings = this.query.split(' ')
            for ( i = 0; i < strings.length; i++) {
                query = strings[i];
                if (query.indexOf('strong>') === -1 && query.length) {
                    query = query.replace(/[\-\[\]{}()*+?.,\\\^$|#\s]/g, '\\$&')
                    result = result.replace(new RegExp('(' + query + ')', 'ig'), function($1, match) {
                        return '<strong>' + match + '</strong>'
                    })
                }
            }
            return result
        },

        render: function(items) {
            var that = this

            items = $(items).map(function(i, rec_no) {
                var lookup;
                that.options.lookup_item.rec_no = rec_no
                lookup = that.options.lookup_item.field_by_name(that.options.field.lookup_field).display_text
                i = $(that.options.item).attr('rec-value', rec_no)
                i.find('a').html(that.highlighter(lookup))
                return i[0]
            })

            items.first().addClass('active')
            this.$menu.html(items)
            return this
        },

        next: function(event) {
            var active = this.$menu.find('.active').removeClass('active'),
                next = active.next()

            if (!next.length) {
                next = $(this.$menu.find('li')[0])
            }

            next.addClass('active')
        },

        prev: function(event) {
            var active = this.$menu.find('.active').removeClass('active'),
                prev = active.prev()

            if (!prev.length) {
                prev = this.$menu.find('li').last()
            }

            prev.addClass('active')
        },

        listen: function() {
            this.$element
                .on('focus', $.proxy(this.focus, this))
                .on('blur', $.proxy(this.blur, this))
                .on('keypress', $.proxy(this.keypress, this))
                .on('keyup', $.proxy(this.keyup, this))

            if (this.eventSupported('keydown')) {
                this.$element.on('keydown', $.proxy(this.keydown, this))
            }

            this.$menu
                .on('click', $.proxy(this.click, this))
                .on('mouseenter', 'li', $.proxy(this.mouseenter, this))
                .on('mouseleave', 'li', $.proxy(this.mouseleave, this))
        },

        eventSupported: function(eventName) {
            var isSupported = eventName in this.$element
            if (!isSupported) {
                this.$element.setAttribute(eventName, 'return;')
                isSupported = typeof this.$element[eventName] === 'function'
            }
            return isSupported
        },

        move: function(e) {
            if (!this.shown) return

            switch (e.keyCode) {
                case 9: // tab
                case 13: // enter
                case 27: // escape
                    e.preventDefault()
                    break

                case 38: // up arrow
                    e.preventDefault()
                    this.prev()
                    break

                case 40: // down arrow
                    e.preventDefault()
                    this.next()
                    break
            }

            e.stopPropagation()
        },

        keydown: function(e) {
            this.suppressKeyPressRepeat = ~$.inArray(e.keyCode, [40, 38, 9, 13, 27])
            this.move(e)
        },

        keypress: function(e) {
            if (this.suppressKeyPressRepeat) return
            this.move(e)
        },

        keyup: function(e) {
            if (!e.ctrlKey && !e.shiftKey) {
                switch (e.keyCode) {
                    case 40: // down arrow
                    case 38: // up arrow
                    case 16: // shift
                    case 17: // ctrl
                    case 18: // alt
                        break

                    case 9: // tab
                    case 13: // enter
                        if (!this.shown) {
                            if (e.keyCode === 13) {
                                this.options.field.select_value();
                            }
                        }
                        else {
                            this.select()
                        }
                        break

                    case 27: // escape
                        if (!this.shown) return
                        this.options.field.update_controls();
                        this.$element.select();
                        this.hide()
                        break

                    default:
                        this.lookup()
                }
                e.stopPropagation()
                e.preventDefault()
            }
        },

        focus: function(e) {
            this.focused = true
        },

        blur: function(e) {
            this.focused = false
            if (!this.mousedover && this.shown) this.hide()
        },

        click: function(e) {
            e.stopPropagation()
            e.preventDefault()
            this.select()
            this.$element.focus()
        },

        mouseenter: function(e) {
            this.mousedover = true
            this.$menu.find('.active').removeClass('active')
            $(e.currentTarget).addClass('active')
        },

        mouseleave: function(e) {
            this.mousedover = false
            if (!this.focused && this.shown) this.hide()
        }

    }


    /* TYPEAHEAD PLUGIN DEFINITION
     * =========================== */

    var old = $.fn.jamtypeahead

    $.fn.jamtypeahead = function(option) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('jamtypeahead'),
                options = typeof option == 'object' && option
            if (!data) $this.data('jamtypeahead', (data = new JamTypeahead(this, options)))
            if (typeof option == 'string') data[option]()
        })
    }

    $.fn.jamtypeahead.defaults = {
        source: [],
        items: 8,
        menu: '<ul class="typeahead dropdown-menu"></ul>',
        item: '<li><a href="#"></a></li>',
        minLength: 1
    }

    $.fn.jamtypeahead.Constructor = JamTypeahead


    /* TYPEAHEAD NO CONFLICT
     * =================== */

    $.fn.jamtypeahead.noConflict = function() {
        $.fn.jamtypeahead = old
        return this
    }


    /* TYPEAHEAD DATA-API
     * ================== */

    $(document).on('focus.jamtypeahead.data-api', '[data-provide="jamtypeahead"]', function(e) {
        var $this = $(this)
        if ($this.data('jamtypeahead')) return
        $this.jamtypeahead($this.data())
    })

}(window.jQuery);
