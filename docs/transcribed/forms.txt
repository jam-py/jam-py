=====
Forms
=====

There are four types of forms: *view forms*, *edit forms*, *filter forms*, 
*param forms*.

These item attributes are JQuery objects:

.. code-block:: js

  > task.invoices.view_form
  > task.invoices.edit_form
  > task.invoices.filter_form
  > task.purchases_report.param_form

You can use JQuery to access any JQuery object in the form

.. code-block:: js

  > // Find and hide new button on the invoices view form
  > task.invoices.view_form.find('#new-btn').hide()

  > // Find ok button on the invoices edit form
  > task.invoices.edit_form.find('#ok-btn')

  > // Find taxrate input line  and change color attribute
  > task.invoices.edit$('input.taxrate').css('color', 'red')

  > // Find tax input line and change color attribute
  > task.invoices.edit_form.find('.dbtable td.tax').css('color', 'red')

You can assign jQuery events to buttons or other form elements.
This is usually done in form events.

Jam.py templates
----------------
Jam.py forms are based on html templates. These templates are defined in the index.html 
file, in the div with the class "templates". When task is loaded it cuts out this div 
and stores it as templates attribute task.

.. code-block:: js

  > task.templates

Forms are created using the create_type_form methods, where type is the type of 
the form. These methods are used internally by the following methods: *view*,  
*insert_record*, *append_record*, *edit_record*.

The application reads the form template from the templates attribute of the task and, 
if the container parameter is passed, inserts it into the container, otherwise a modal 
form is created and the template is inserted into it.

The application first looks for a template with a formname-type class, where formname 
is the item_name attribute of the form, and type is the form type.

.. note::
	Form example: customers-view

If the template is not found, it looks for the owner template, and after that the default 
template.

Items have type_options attributes, where type is a form type that specifies the attributes 
of the form to create. For more information on form options, see the documentation.

.. code-block:: js

  > task.invoices.view_options
  {title: "Invoices", fields: Array(9), form_header: true, form_border: true, close_button: true,...}

  > task.invoices.edit_options
  {title: "Invoices", fields: Array(0), form_header: true, form_border: true, close_button: true,...}
