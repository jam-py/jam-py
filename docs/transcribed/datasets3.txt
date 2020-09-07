===============================
Working with data on the server
===============================

Call *server* javascript function
-------------------------------
Let's defined the delete_all function on the server

.. code-block:: py

  def delete_all(item):
      c = item.copy()
      c.open()
      c.first()
      while not c.eof():
          c.delete()
      c.apply()

And execute it using the server method. After the execution, we call the open method
to display the changes.

.. code-block:: py

  task.catalog.server('delete_all', function() {
      task.catalog.open(true)
  })

.. note::
	Functions on the server can be executed in parallel threads. Always create 
	copies of items when working with datasets.

Let's we defined the function for add records to the table:

.. code-block:: py

  def add_records(item, count):
      c = item.copy()
      c.open()
      for i in range(count):
          c.append();
          c.name.value = 'Record %s' % (i + 1)
          c.value.value = i + 1;
          c.post();
      c.apply()

  task.catalog.server('add_records', [100], function() {
      task.catalog.open(true)
  })

Now we defined the function for change records:

.. code-block:: py

  def change(item, delta):
      copy = item.copy()
      copy.open()
      for c in copy:
          c.edit()
          c.value.value += delta;
          c.post();
      copy.apply()
  
  task.catalog.server('change', [1000], function() {
      task.catalog.open(true)
  })

As you can see, the methods of working with datasets on the server are the same 
as those on the client. 

You can pass the options dictionary to the open method in the same way as on 
the client.

.. code-block:: py

  def list_records(item):
      copy = item.copy()
      copy.open({'fields': ['value', 'name'], 'where': {'value__ge': 1090}, 'order_by': ['-value']})
      for c in copy:
          print c.name.value, c.value.value
  
  task.catalog.server('list_records', true)

Or pass these parameters as keyword arguments:

.. code-block:: py

  def list_records(item):
      copy = item.copy()
      copy.open(fields=['value', 'name'], where={'value__ge': 1090}, order_by=['-value', 'name'])
      for c in copy:
          print c.name.value, c.value.value

  task.catalog.server('list_records', true)

The same is for the *set_where*, *set_fields*, *set_order_by* methods.For example, 
the the result of the execution of following pairs of functions is the same:

.. code-block:: py

  item.set_where({'value__ge': 1090, 'date__gt': now})
  item.set_where(value__ge=1090, date__gt=now)

  copy.set_fields(['value', 'name'])
  copy.set_fields('value', 'name')

  copy.set_order_by(['-value', 'name'])
  copy.set_order_by('-value', 'name')

Call execute methods of the task module
---------------------------------------
Another way to work with database data is to use the *execute* and *execute_select*
methods of the task. These methods use the application connection pool. We will 
also use the *table_name* attribute of the item.

Use the *execute_select* method to execute the sql select query. This method returns 
a list of records:

.. code-block:: py

  def pool_execute_select(item):
      res = item.task.execute_select('select name, value from %s where deleted = 0' % item.table_name)
      for r in res:
          print r
  
  task.catalog.server('pool_execute_select', true)

.. note::
	For the catalog item, the value of the 'Soft Delete' attribute is set to true, 
	which means that the delete method does not remove the record from the table, 
	but uses the deleted field to mark the record as deleted. The item's open method 
	takes this into account, in all other cases you must add  this condition: 
	deleted = 0.

.. code-block:: py

  def pool_execute_select(item):
      res = item.task.execute_select('select count(*) from %s where deleted = 0' % item.table_name)
      print 'not deleted', res
      res = item.task.execute_select('select count(*) from %s' % item.table_name)
      print 'all', res

Let's empty the catalog table and add 10 records using the *execute* method of the task

.. code-block:: py

  def pool_execute(item):
      delete_sql = 'delete from %s' % item.table_name
      add_sql = []
      for i in range(10):
          add_sql.append("insert into %s (value, name, deleted) values (%d, '%s', 0)" % 
              (item.table_name, i + 1, 'Record %s' % (i + 1)))
      item.task.execute([delete_sql] + add_sql)
  
  task.catalog.server('pool_execute', function() {
      task.catalog.open(true)
  })


.. note::
  The parameter of the execute methods can be a query string, a list of query strings, 
  a list of lists and so on. 

.. note::
  All queries are executed in one transaction and if execution succeeds the commit 
  command is called, otherwise rollback command is executed.

Third way to read or write database data is to create a connection using 
the *create_connection* method of the task or using the sqlite3 connect function 
(for a SQLITE database)

.. code-block:: py

  def use_connection(item):
      con = item.task.create_connection()
      cur = con.cursor()
      cur.execute('delete from %s' % item.table_name)
      for i in range(10):
          cur.execute("insert into %s (value, name, deleted) values (%d, '%s', 0)" % 
              (item.table_name, i + 1, 'Record %s' % (i + 1)))
      con.commit()
      con.close()
  
  task.catalog.server('use_connection', function() {
      task.catalog.open(true)
  })

.. code-block:: py
  
  import sqlite3
  def sqlite3_connection(item):
      con = sqlite3.connect('ds.sqlite')
      cur = con.cursor()
      cur.execute('delete from %s' % item.table_name)
      for i in range(20):
          cur.execute("insert into %s (value, name, deleted) values (%d, '%s', 0)" % 
              (item.table_name, i + 1, 'Record %s' % (i + 1)))
      con.commit()
      con.close()
  
  task.catalog.server('sqlite3_connection', function() {
      task.catalog.open(true)
  })


.. note::
	Do not forget to close the connection.