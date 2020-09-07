===================
Data aware controls
===================

The *create_table* method
-------------------------
Let's clear the div with the id = 'content' and add a div with the id = 'table' to it.

.. code-block:: js

  $('#content').empty()
  $('#content').append($("<div id='table'>"))

Now we create a copy of the customers item, call the create_table method and fill it 
with data, calling the open method.

.. code-block:: js

  c = task.customers.copy()
  c.create_table($('#table'))
  c.open()

Let's close the customer item and set its paginate attribute to true.

.. code-block:: js

  c.close()
  c.paginate = true

When this attribute is set, the create_table method calculates the number of rows for 
a given table height (the default value is 480 pixels) and creates a pagination control.

.. code-block:: js

  c.create_table($('#table'))

The open method retrieves from the server the number of records calculated by the table

.. code-block:: js

  c.open()

Now the table loads records from the server, when necessary.

Let's display records of customers from Germany:

.. code-block:: js

  c.set_where({country: 'Germany'})
  c.open()

Now we show all customers:

.. code-block:: js

  c.open()

The create_table method has many options. Let's change, for example, the displayed 
fields and the height of the table.


.. code-block:: js

  c.create_table($('#table'), {fields: ['firstname', 'lastname'], height: 600})
  c.open()

For other options, see the documentation.

The *create_input* method
-------------------------

.. code-block:: js

  c.create_table($('#table'))
  c.open()

Now we will demonstrate the create_input method and, to do this, we will add a div with 
id = 'fields' to the div with id = 'content':

.. code-block:: js

  $('#content').append($("<div id='fields'>"))

  c.create_inputs($('#fields'))
  c.create_inputs($('#fields'), {col_count: 2})
  c.create_inputs($('#fields'), {fields: ['firstname', 'lastname'], col_count: 2})
  c.create_inputs($('#fields'), {col_count: 2, label_on_top: true})
  c.create_inputs($('#fields'), {col_count: 3})
  c.create_inputs($('#fields'), {col_count: 3, label_width: 90})

To complete this demo, let's allow the user to edit the records of the customers item.

.. code-block:: js

  c.on_after_scroll = function(item) {
    if (item.record_count()) 
      item.edit();
  }

Records are changed on the client, but these changes are not saved in the database.
To save the changes, let's add one more event handler:

.. code-block:: js

  c.on_before_scroll = function(item) { 
    item.apply();
  }

To learn how *edit*, *apply*, *on_before_scroll*, *on_after_scroll* work, see 
the following videos.


.. note::

 We used a copy of the customers item to prevent the behavior of the customers item itself 
 from changing, the event handlers that we added are only associated with the copy.

There are two other methods: *create_filter_inputs* and *create_param_inputs*. They work 
just like create_inputs, but they are used to edit filters values of data items and 
parameter values of report items.
