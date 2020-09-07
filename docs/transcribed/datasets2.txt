==========
Datasets 2
==========
Before we start, we will create a copy of the catalog item and make a table to 
display data.

.. code-block:: js

  c = task.catalog.copy()
  c.create_table($('#content'), {height: 820})
  c.open(true)

Asynchronously and synchronously function calls
-----------------------------------------------
The open and apply methods can have callback and async parameters. If callback 
function is passed as a parameter or one of parameters is true, the request to 
the server is executed asynchronously, and after that, as the dataset is received, 
the callback function, if defined, will be executed.

.. code-block:: js

  c.open( function() { 
    c.warning(c.record_count()) 
  } )

  c.open(true)

Otherwise the request is executed synchronously.

.. code-block:: js

  c.open()

The *open* method
-----------------
It can have the following parameters: options, callback, async.
Options parameter is an object that can have the following attributes:
*expanded*, *fields*, *where*, *order_by*, *open_empty*, *funcs*, *group_by*, 
*limit*, *offset*.

.. code-block:: js

  options = {
      where: {value__range: [10, 20]},
      fields: ['name', 'value'],
      order_by: ['-value']
  }
  
  callback = function(item) {
      item.warning('Total records: ' + item.record_count())
  }
  
  c.open(options, callback)

The order of parameters doesn't matter. Some parameters can be omitted!
Let's demonstrate the *func* parameter:

.. code-block:: js

  c.open(
      {
          where: {value__range: [10, 20]},
          fields: ['value'],
          funcs: {value: 'sum'}
      },
      true
  )

There are auxiliary methods: *set_where*, *set_fields*, *set_order_by*. Calling 
these methods before the open method is similar to specifying corresponding parameters

.. code-block:: js

  c.open({
      where: {value__range: [10, 20]},
      fields: ['name', 'value'],
      order_by: ['-value']
    },
    callback
  )

It is the same as:

.. code-block:: js

  c.set_where( {value__range: [10, 20]} )
  c.set_fields( ['name', 'value'] )
  c.set_order_by( ['-value'] )
  c.open(callback)

After calling the open method, the action of these methods is canceled.

.. code-block:: js

  c.open(true)

This can be used, for example, by setting filtering before calling the view method, 
which calls the open method in the *on_view_form_created* event handler.

.. code-block:: js

  task.catalog.set_where( {value__range: [10, 60]} )
  task.catalog.view()

Filtering of the records
------------------------
There are three ways to define what records an item dataset will get from the database 
table:

1. When the open method is called specify *where* parameter, 
2. Call the *set_where* method, before calling the open method, 
3. Use filters.

Let's we create the *value_ge* filter for the value field, with filter type GE 
(greater than or equal to). Let's set its value to 50.

.. code-block:: js

    c.filters.value_ge.value = 50
    c.open(true)

Filtering is performed as follows:

* When where parameter is specified, it is always used, even if the *set_where* 
  method was called or the element has filters whose values are set.

  .. code-block:: js

    c.set_where({value__ge: 10})
    c.open({where: {value__ge: 90}}, true)

* When where parameter is omitted the parameter passed to the *set_where* method 
  is used.

  .. code-block:: js

    c.set_where({value__ge: 10})
    c.open(true)

* When the *where* parameter is omitted and the *set_where* method was not called, 
  filters are used

  .. code-block:: js

    c.open(true)

To disable a filter set its value to null

.. code-block:: js

  c.filters.value_ge.value = null
  c.open(true)

The *where* parameter of the open method is a dictionary, whose keys are names 
of the fields that are followed, after double underscore, by a filter symbol.

.. note::
	| For EQ (equal) filter the filtering symbol *__eq* can be omitted. 
	| For example {id: 100} is equivalent to {id__eq: 100}.

For more information, see the Documentation.