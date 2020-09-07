========
Datasets
========

For this session, we create a simple application. Let's call it *Datasets*, and 
let's create one catalog item, called *Catalog*. Let this item have two fields:

* *name*, type of text, lenght = 256,
* *value*, type of integer.

Before we start, we will create a copy of the catalog item and create a table to 
display its data:

.. code-block:: js

  c = task.catalog.copy()
  c.create_table($('#content'), {height: 820})

Dataset
  A *dataset* is set of data records, stored in memory. 
  
Before we can use a dataset we have to call the *open* method of the Catalog item. 
This method sends a request to the server to get dataset from catalog database table.

.. code-block:: js

  c.open(true)
  
Since the table is empty, the dataset does not contain any record. We can verify 
this by calling the *record_count* method.

.. code-block:: js

  c.record_count()           // 0
  
Let's fill dataset with records:

.. code-block:: js

  for (var i = 0; i < 10 ; i++ ) {
    c.append();
    c.name = 'Record ' + (i + 1);
    c.value.value = i + 1;
    c.post;
  }
  
Now, we can navigate the dataset:

.. code-block:: js

  // Go to the first record in the dataset
  c.first()
  
  // Go to the last record in the dataset
  c.last()
  
  // rec_no gets or sets the record number of the curent record
  c.rec_no                   // 9
  
  c.rec_no = 5               // 5
  
  // Go to the next record in the dataset
  c.next()
  
  // Go to the previously record in the dataset
  c.prior()
  
There are two metods, the *bof()* and *eof()*, that return true if an atempt is 
made to go beyond the first or the last record.

Now we can go through all records in the dataset:

.. code-block:: js

  c.first()
  while(!c.eof()) {
    console.log(c.name.value);
    c.next();
  }

There is another way to iterate over the dataset records on the client:

.. code-block:: js

  c.each(function(c) {
      console.log(c.name.value);
  })

We can stop iteration by returning false:

.. code-block:: js

  c.each(function(c) {
      console.log(c.name.value);
      if (c == 5) {
        retun false;
      }
  })

To change the record, we need to set the dataset in edit mode. This is done by 
calling the edit method.

.. code-block:: js

  c.edit()
  
When the record is in edit mode, the *is_edited* and *is_changing* methods return 
true.

.. code-block:: js

  c.is_edited()              // true
  
  c.is_changing()            // true
  
To save changes in memory, call the *post* method. The post method is automatically 
called when dataset cursor moves to another record.

.. code-block:: js

  c.value.value = 5000
  c.post()
  
  c.is_edited()              // false
  
  c.is_changing()            // false

.. note::
 When you try to change values of the fields, when dataset is not in edit mode, 
 an exception is thrown.
 
When we append a new record or insert a record:

.. code-block:: js
  
  c.append()
  
  c.is_new()                 // true
  
  c.is_changing()            // true
  
  c.value.value = 11
  
  c.insert()  
  
  c.value.value = -1
  
To cancel edit or append/insert operation call the *cancel* method.

.. code-block:: js
  
  c.cancel()
  
To delete a record call the *delete* method.

.. code-block:: js
  
  c.delete()

This method deletes the record and moves cursor on to the next record. This way, 
we can delete all records in the datase.

.. code-block:: js

  c.first()
  while(!c.eof()) {
    c.delete();
  }

Now we add 500 records:

.. code-block:: js

  for (var i = 0; i < 500 ; i++ ) {
    c.append();
    c.name = 'Record ' + (i + 1);
    c.value.value = i + 1;
    c.post;
  }

Every time the addition, modification or deletion of a record occurs, visual contols
display these changes. This can take quite some time. To avod this you can use 
following methods: *disable_controls*, *enable_controls*, *update_controls*.

.. code-block:: js

  // Add 2000 records
  c.disable_controls()
  try {
    for (var i = 0; i < 2000 ; i++ ) {
      c.append();
      c.name = 'Record ' + (i + 1);
      c.value.value = i + 1;
      c.post;
    }
  }
  finally {
    c.enable_controls();
    c.update_controls();
  }

  c.record_count()           // 2500
  
Now we can delete all of 2500 records

.. code-block:: js
  
  c.disable_controls()
  try {
    c.first()
    while(!c.eof()) {
      c.delete();
    }
  }
  finally {
    c.enable_controls();
    c.update_controls();
  }

Let's add records again.
  
.. code-block:: js
  
  c.disable_controls()
  try {
    for (var i = 0; i < 1000 ; i++ ) {
      c.append();
      c.name = 'Record ' + (i + 1);
      c.value.value = i + 1;
      c.post;
    }
  }
  finally {
    c.enable_controls();
    c.update_controls();
  }

These records are stored in memory, and the table in the database is empty. If we 
call the open metod, the resulting dataset will also be empty.

.. code-block:: js

  c.record_count()           // 1000 records in memory
  
  c.open(true)               // gets records from the database table
  
  c.record_count()           // 0 records in the database table,
                             // because apply method didn't called 

Data items stores log of all changes to the dataset, if *log_changes* attribute 
is set to true.

.. code-block:: js

  c.log_changes             // true

  c.disable_controls()
  try {
    for (var i = 0; i < 1000 ; i++ ) {
      c.append();
      c.name = 'Record ' + (i + 1);
      c.value.value = i + 1;
      c.post;
    }
  }
  finally {
    c.enable_controls();
    c.update_controls();
  }
  
  c.edit()
  
  c.value.value = 1000000
  
  c.apply(true)
  
  // Let's delete the records
  c.disable_controls()
  try {
    c.first()
    while(!c.eof()) {
      c.delete();
    }
  }
  finally {
    c.enable_controls();
    c.update_controls();
  }

  c.open(true)
  
  c.record_count()         // 1000
  
Thus, the open method reads the dataset from the database table, and the apply 
method writes the changes made to the dataset into the database.

There are many events triggered by these methods. The *on_before_scroll* and 
*on_after_scroll* occurs before and after an application scrolls from one record 
to another. The on_before_scroll and the on_after_scroll ocurs before and after 
an application scrolls from one record to another.

For following methods: *append*, *insert*, *edit*, *cancel*, *post* and *apply*, 
*on_before* event is triggered before these metods are called. You can abort 
execution of this methods by throwing an exception or calling the *abort* method.

.. code-block:: js

  c.on_before_scroll = function(item) {
    item.abort('No way');
  }
  
When you try to move from the current records, an exception will appear, with 
the text "No way".

Now we define *before_post* event handler

.. code-block:: js

  c.on_before_scroll = undefined
  
  c.before_post = function(item) {
    c.name.value = 'record' + c.value.value;
  }
  
  c.append()
  c.value.value = 1001          // c.name.value = 1001












