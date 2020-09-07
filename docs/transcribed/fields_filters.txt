==================
Fields and filters
==================
For this session, we created a journal, with name journal, with different types 
of fields: *currency*, type of currency, *date*, type of date, *integer*, type of 
integer, *lookup*, type of integer, lookup_item is catalog, *lookup_value*, type of 
integer, lookup_value is catalog.value.

All items except reports have a *fields* attribute - a list of field objects that 
are used to represent fields in the dataset: 

.. code-block:: js

  task.journal.fields

Let's loop over fields

.. code-block:: js

  for (var i = 0; i < task.journal.fields.length; i++) {
      var field = task.journal.fields[i];
      console.log(field.field_name, field.field_caption);
  }

Another way to loop over fields is to use the *each_field* method

.. code-block:: js

  task.journal.each_field(function(field) {
      console.log(field.field_name, field.field_caption);
  });

As you can see, there are two fields that are not displayed. These are common fields 
declared in the item group.

In addition to the *field_name* attribute that is used in the code, and the *caption_name*
attribute that is displayed to the user, the field object has the *owner* attribute 
that specifies the item to which this field belongs. And every field is an attribute 
of the item that owns it.

.. code-block:: js

  task.journal.date
  task.journal.date.owner
  task.journal.date.owner.currency
  task.journal.date.owner.currency.owner

Access to the item dataset
--------------------------
To access the item dataset, the field object have the following properties: *data*, 
*value*, *text*, *lookup_value*, *lookup_text*, *display_text*.

* To get or set the field's value of the current record use the *value* property:

  .. code-block:: js

    task.journal.date.value
    task.journal.currency.value

  .. note::
    When reading, the value is converted to the type of a field. So for fields of type 
    integer, float and currency, if the value of this field is *null*, the value returned 
    by this property is 0.

* To get an unconverted value use the *data* property.

  .. code-block:: js

    task.journal.currency.data

* To get or set the value of a field as text use the *text* property.

  .. code-block:: js

    task.journal.currency.text

* There are two lookup fields - lookup and lookup_value. The lookup field is a master
  field for the lookup_value field. These fields have the same value property. It is
  a value of the primary field "id" in the catalog item that is a lookup item for 
  this fields.

  .. code-block:: js
  
    task.journal.lookup.value
    task.journal.lookup_value.value
  
  For lookup fields there is a *lookup_value* and *lookup_text* properties.
  
  .. code-block:: js
  
    task.journal.lookup.lookup_value
    task.journal.lookup_value.lookup_value

* To get the text displayed to the user by visual controls, use the the *display_text* property.
  
* For the date, time, currency and float fields, the text displayed to the user 
  is determined by the parameters set in the locale.

  .. code-block:: js

    --%d.%m.%Y
    %Y-%m-%d

.. note::
	Data and display_text properties are read-only, 
	
.. note::
  The changes to lookup_value and lookup_text properties are not stored in the database.

Field event handlers
--------------------
Items generate some events associated with fields. With event handlers that process 
this events is passed as a parameter the associated field. 

You can change how visual controls display the field value by writing the *on_field_get_text*
handler.

.. code-block:: js

  function on_field_get_text(field) {
      if (field.field_name === 'date') {
          return field.value.toDateString();
      }
  }

Write an *on_field_changed* event handler to respond to any changes in the field’s data.

.. code-block:: js

  function on_field_changed(field, lookup_item) {
      var item = field.owner;
      if (field.field_name === 'integer') {
          item.currency.value = field.value * 1000;
      }
  }

.. note::
	This event is generated every time field value changes. This can lead to an infinite 
	looping.

For example:

.. code-block:: js

  function on_field_changed(field, lookup_item) {
      if (field.field_name === 'integer') {
          field.value = field.value + 1;
      }
  }

In this case, you can do the following to prevent code execution after changing 
the value of the field:

.. code-block:: js
  
  function on_field_changed(field, lookup_item) {
      if (field.field_name === 'integer') {
          if (!field._calculating) {
              field._calculating = true;
              try {
                  field.value = field.value + 1;
              }
              finally {
                  field._calculating = false;
              }
          }
      }
  }

The *lookup_item* parameter is specified when the user changes the lookup field by 
selecting it from lookup item or using typeahead:

.. code-block:: js

  function on_field_changed(field, lookup_item) {
      if (lookup_item) {
          console.log(lookup_item.item_name, lookup_item.id.value);
      }
  }
  
Write the *on_field_validate* event handler to check the changes made to the field.
We will assign it dynamically:

.. code-block:: js
  
  task.journal.on_field_validate = function(field) {
      if (field.field_name === "integer" && field.value < 0) {
          return 'Field value must be greater than zero';
      }
  }

.. note::
	The above code can be placed anywhere in the jam.py code and even in some other 
	event handler. In other words, it may take different forms depending on the value 
	of some external variables or fields.

Write the *on_field_select_value* event handler to specify fields that will be displayed, 
set up filters for the lookup item.

.. code-block:: js
  
  function on_field_select_value(field, lookup_item) {
      if (field.field_name === 'lookup') {
          lookup_item.view_options.fields = ['value', 'name']
          lookup_item.set_where({value__range:  [1, 10]});
      }
  }

Filters
-------
All items have a filters attribute - a list of filter objects that are used to visually 
determine the request parameters made by the application to the project database.
Let's loop over filters:

.. code-block:: js

  for (var i = 0; i < task.journal.filters.length; i++) {
      var filter = task.journal.filters[i];
      console.log(filter.filter_name, filter.filter_caption);
  }

Another way to loop over filters is to use the *each_filter* method:

.. code-block:: js

  task.journal.each_filter(function(filter) {
      console.log(filter.filter_name, filter.filter_caption);
  });

You can access the filter object as follows:

.. code-block:: js

  task.journal.filters.date

To get or set filter value use filter value property

.. code-block:: js

  task.journal.filters.date.value = new Date()
  task.journal.open(true)

.. note::
	Items can generate some events associated with filters. 
