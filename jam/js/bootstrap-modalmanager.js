/* ===========================================================
 * bootstrap-modalmanager.js v2.1
 * ===========================================================
 * Copyright 2012 Jordan Schroter.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ========================================================== */

!function ($) {

    "use strict"; // jshint ;_;

    /* MODAL MANAGER CLASS DEFINITION
    * ====================== */

    var ModalManager = function (element, options) {
        this.init(element, options);
    };

    ModalManager.prototype = {

        constructor: ModalManager,

        init: function (element, options) {
            var that = this;
            this.$element = $(element);
            this.options = $.extend({}, $.fn.modalmanager.defaults, this.$element.data(), typeof options == 'object' && options);
            this.stack = [];
            this.backdropCount = 0;

            if (this.options.resize) {
                var resizeTimeout;
                $(window).on('resize.modal', function(){
                    resizeTimeout && clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(function(){
                        for (var i = 0; i < that.stack.length; i++){
                            that.stack[i].isShown && that.stack[i].layout();
                        }
                    }, 100);
                });
            }
        },

        createModal: function (element, options) {
            $(element).modal($.extend({ manager: this }, options));
        },

        topModal: function() {
            var i,
                result;
            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].isShown) result = this.stack[i];
            }
            return result;
        },

        appendModal: function (modal) {
            var that = this,
                i,
                topModal = this.topModal();
            if (!topModal) {
                this.activeElement = $(':focus').get(0);
            }

            modal.zPos = this.getMaxzPos() + 1;
            this.stack.push(modal);

            modal.$element.on('show.modalmanager', targetIsSelf(function (e) {

                var showModal = function(){
                    modal.isShown = true;

                    var transition = $.support.transition && modal.$element.hasClass('fade');

                    that.$element
                        .toggleClass('modal-open', that.hasOpenModal())
                        .toggleClass('page-overflow', $(window).height() < that.$element.height());

                    modal.$parent = modal.$element.parent();

                    modal.$container = that.createContainer(modal);

                    modal.$element.appendTo(modal.$container);

                    modal.layout();

                    that.backdrop(modal, function () {

                        modal.$element.show();

                        if (transition) {
                            //modal.$element[0].style.display = 'run-in';
                            modal.$element[0].offsetWidth;
                            //modal.$element.one($.support.transition.end, function () { modal.$element[0].style.display = 'block' });
                        }

                        modal.$element
                            .addClass('in')
                            .attr('aria-hidden', false);

                        var complete = function () {
                            that.setFocus();
                            modal.$element.trigger('shown');
                        };

                        transition ?
                            modal.$element.one($.support.transition.end, complete) :
                            complete();
                    });
                };

                modal.options.replace ?
                    that.replace(showModal) :
                    showModal();
            }));

            modal.$element.on('hidden.modalmanager', targetIsSelf(function (e) {

                that.backdrop(modal);

                if (modal.$backdrop){
                    $.support.transition && modal.$element.hasClass('fade') ?
                        modal.$backdrop.one($.support.transition.end, function () { that.destroyModal(modal) }) :
                        that.destroyModal(modal);
                } else {
                    that.destroyModal(modal);
                }

            }));

            modal.$element.on('destroy.modalmanager', targetIsSelf(function (e) {
                that.removeModal(modal);
            }));
        },

        destroyModal: function (modal) {
            var self = this,
                timeout;
            modal.destroy();
            var hasOpenModal = this.hasOpenModal();

            this.$element.toggleClass('modal-open', hasOpenModal);

            if (!hasOpenModal){
                this.$element.removeClass('page-overflow');
            }

            this.removeContainer(modal);


            timeout = setTimeout(function () {
                    self.restoreFocus();
                }, 100
            );
        },

        hasOpenModal: function () {
            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].isShown) return true;
            }
            return false;
        },

        restoreFocus: function () {
            var topModal;
            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].isShown) topModal = this.stack[i];
            }
            if (topModal) {
                topModal.restoreFocus();
            }
            else {
                $(this.activeElement).focus();
            }
        },

        setFocus: function () {
            var topModal,
                tag;

            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].isShown) topModal = this.stack[i];
            }

            if (topModal) {
                tag = $(topModal.tabList()).eq(0);
                topModal.focus();
                if (tag.length) {
                    setTimeout(function()
                        {tag.focus()},
                        100
                    );
                }
            }
        },

        removeModal: function (modal) {
            modal.$element.off('.modalmanager');
            if (modal.$backdrop) this.removeBackdrop(modal);
            this.stack.splice(this.getIndexOfModal(modal), 1);
        },

        getModalAt: function (index) {
            return this.stack[index];
        },

        getIndexOfModal: function (modal) {
            for (var i = 0; i < this.stack.length; i++){
                if (modal === this.stack[i]) return i;
            }
        },

        getMaxzPos: function() {
            var result = 0;
            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].zPos > result) {
                    result = this.stack[i].zPos;
                }
            }
            return result;
        },

        replace: function (callback) {
            var topModal;

            for (var i = 0; i < this.stack.length; i++){
                if (this.stack[i].isShown) topModal = this.stack[i];
            }

            if (topModal) {
                this.$backdropHandle = topModal.$backdrop;
                topModal.$backdrop = null;

                callback && topModal.$element.one('hidden',
                    targetIsSelf( $.proxy(callback, this) ));

                topModal.hide();
            } else if (callback) {
                callback();
            }
        },

        removeBackdrop: function (modal) {
            modal.$backdrop.remove();
            modal.$backdrop = null;
        },

        createBackdrop: function (animate) {
            var $backdrop;

            if (!this.$backdropHandle) {
                $backdrop = $('<div class="modal-backdrop ' + animate + '" />')
                    .appendTo(this.$element);
            } else {
                $backdrop = this.$backdropHandle;
                $backdrop.off('.modalmanager');
                this.$backdropHandle = null;
                this.isLoading && this.removeSpinner();
            }

            return $backdrop;
        },

        removeContainer: function (modal) {
            modal.$container.remove();
            modal.$container = null;
        },

        createContainer: function (modal) {
            var $container;

            //~ $container = $('<div class="modal-scrollable">')
                //~ .css('z-index', getzIndex( 'modal',
                    //~ modal ? this.getIndexOfModal(modal) : this.stack.length ))
                //~ .appendTo(this.$element);
            $container = $('<div class="modal-scrollable">')
                .css('z-index', getzIndex('modal', modal.zPos))
                .appendTo(this.$element);


            if (modal && modal.options.backdrop != 'static') {
                $container.on('click.modal', targetIsSelf(function (e) {
                    modal.hide();
                }));
            } else if (modal) {
                $container.on('click.modal', targetIsSelf(function (e) {
                    modal.attention();
                }));
            }

            return $container;

        },

        backdrop: function (modal, callback) {
            var animate = modal.$element.hasClass('fade') ? 'fade' : '',
                showBackdrop = modal.options.backdrop &&
                    this.backdropCount < this.options.backdropLimit;

            if (modal.isShown && showBackdrop) {
                var doAnimate = $.support.transition && animate && !this.$backdropHandle;

                modal.$backdrop = this.createBackdrop(animate);

//                modal.$backdrop.css('z-index', getzIndex( 'backdrop', this.getIndexOfModal(modal) ));
                modal.$backdrop.css('z-index', getzIndex( 'backdrop', modal.zPos ));

                if (doAnimate) modal.$backdrop[0].offsetWidth; // force reflow

                modal.$backdrop.addClass('in');

                this.backdropCount += 1;

                doAnimate ?
                    modal.$backdrop.one($.support.transition.end, callback) :
                    callback();

            } else if (!modal.isShown && modal.$backdrop) {
                modal.$backdrop.removeClass('in');

                this.backdropCount -= 1;

                var that = this;

                $.support.transition && modal.$element.hasClass('fade')?
                    modal.$backdrop.one($.support.transition.end, function () { that.removeBackdrop(modal) }) :
                    that.removeBackdrop(modal);

            } else if (callback) {
                callback();
            }
        },

        removeSpinner: function(){
            this.$spinner && this.$spinner.remove();
            this.$spinner = null;
            this.isLoading = false;
        },

        removeLoading: function () {
            this.$backdropHandle && this.$backdropHandle.remove();
            this.$backdropHandle = null;
            this.removeSpinner();
        },

        loading: function (callback) {
            callback = callback || function () { };

            this.$element
                .toggleClass('modal-open', !this.isLoading || this.hasOpenModal())
                .toggleClass('page-overflow', $(window).height() < this.$element.height());

            if (!this.isLoading) {

                this.$backdropHandle = this.createBackdrop('fade');

                this.$backdropHandle[0].offsetWidth; // force reflow

                this.$backdropHandle
                    .css('z-index', getzIndex('backdrop', this.stack.length))
                    .addClass('in');

                var $spinner = $(this.options.spinner)
                    .css('z-index', getzIndex('modal', this.stack.length))
                    .appendTo(this.$element)
                    .addClass('in');

                this.$spinner = $(this.createContainer())
                    .append($spinner)
                    .on('click.modalmanager', $.proxy(this.loading, this));

                this.isLoading = true;

                $.support.transition ?
                    this.$backdropHandle.one($.support.transition.end, callback) :
                    callback();

            } else if (this.isLoading && this.$backdropHandle) {
                this.$backdropHandle.removeClass('in');

                var that = this;
                $.support.transition ?
                    this.$backdropHandle.one($.support.transition.end, function () { that.removeLoading() }) :
                    that.removeLoading();

            } else if (callback) {
                callback(this.isLoading);
            }
        },

        elzIndex: function(el) {
            var result = 0,
                parent;
            if (el && el.parentNode) {
                parent = el.parentNode;
                while (parent) {
                    if (parent.className && parent.className === 'modal-scrollable') {
                        result = $(parent).css('z-index');
                    }
                    parent = parent.parentNode;
                }
            }
            return result;
        }
    };

    /* PRIVATE METHODS
    * ======================= */

    // computes and caches the zindexes
    var getzIndex = (function () {
        var zIndexFactor,
            baseIndex = {};

        return function (type, pos) {

            if (typeof zIndexFactor === 'undefined'){
                var $baseModal = $('<div class="modal hide" />').appendTo('body'),
                    $baseBackdrop = $('<div class="modal-backdrop hide" />').appendTo('body');

                baseIndex['modal'] = +$baseModal.css('z-index');
                baseIndex['backdrop'] = +$baseBackdrop.css('z-index');
                zIndexFactor = baseIndex['modal'] - baseIndex['backdrop'];

                $baseModal.remove();
                $baseBackdrop.remove();
                $baseBackdrop = $baseModal = null;
            }

            return baseIndex[type] + (zIndexFactor * pos);

        }
    }());

    // make sure the event target is the modal itself in order to prevent
    // other components such as tabsfrom triggering the modal manager.
    // if Boostsrap namespaced events, this would not be needed.
    function targetIsSelf(callback){
        return function (e) {
            if (this === e.target){
                return callback.apply(this, arguments);
            }
        }
    }

    /* MODAL MANAGER PLUGIN DEFINITION
    * ======================= */

    $.fn.modalmanager = function (option, args) {
        return this.each(function () {
            var $this = $(this),
                data = $this.data('modalmanager');

            if (!data) $this.data('modalmanager', (data = new ModalManager(this, option)));
            if (typeof option === 'string') data[option].apply(data, [].concat(args))
        })
    };

    $.fn.modalmanager.defaults = {
        backdropLimit: 999,
        resize: true,
        spinner: '<div class="loading-spinner fade" style="width: 200px; margin-left: -100px;"><div class="progress progress-striped active"><div class="bar" style="width: 100%;"></div></div></div>'
    };

    $.fn.modalmanager.Constructor = ModalManager

    var manager = $('body').data('modalmanager');

    if (!manager) {
        manager = $('body').modalmanager().data('modalmanager');
    }

    $(window).on('keydown.modalmanager keyup.modalmanager keypress.modalmanager', function(e) {
        var topModal = manager.topModal();
        if (topModal && e.target) {
            if (manager.elzIndex(e.target) < topModal.zIndex) {
                e.stopImmediatePropagation();
                e.stopPropagation();
                e.preventDefault();
                topModal.restoreFocus();
            }
        }
    });

}(jQuery);
