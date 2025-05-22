
[![Package on PyPI](https://img.shields.io/pypi/v/jam.py-v7.svg)](https://pypi.org/project/jam.py-v7) ![Supported Python versions](https://img.shields.io/pypi/pyversions/python3-saml.svg) [![Documentation Status](https://readthedocs.org/projects/jampy-docs-v7/badge/)](https://jampy-docs-v7.readthedocs.io) [![Downloads](https://static.pepy.tech/badge/jam.py-v7)](http://pepy.tech/project/jam.py-v7)


## Jam.py Application Builder (web framework)

## This is forked jam.py to continue the support and development, since Andrew is retiring from jam.py project. The GH organisation name is jam.py-v5, since we are hoping to release official v7 this year (2025). 


Jam.py is powerful Web Application Builder for managing data effortlessly. All batteries included. Plus, it is event driven! What is EDA:

"An event-driven framework, also known as event-driven architecture (EDA), is a design pattern where software components communicate and react to changes in state or events." Everyhing in Jam.py can be an event. Like a mouse click, or pressing CRTL+Ins, CTRL+Del or whatever is defined by you.

Another major difference from other products is that the entire application is contained within a **single SQLite3 file**. And it can be **encrypted**! 

Another key distinction is the ability to run **any Python procedure directly within the Application Builder** - including popular libraries like Matplotlib, Pandas, and NumPy - with the results displayed in the browser. Python procedure can run **synchronously** or **asynchronously** on the server. There's no need to access the console to review logs anymore, the **server sends results** to the browser!

More over, using **Import tables** feature from any supported database is providig instant data access! There's no need to code anything and **authentication is one click away**! 

Hope this sparked some interest! Thank you.

[![alt text](https://github.com/jam-py-v5/jam-py/blob/develop/assets/images/JAMPY_Readme.gif?raw=true)](https://northwind.pythonanywhere.com)


Some short videos about how to setup Jam.py and create applications:

* [Creating CRM web database applications from start to finish in 7 minutes with Jam.py framework](https://youtu.be/vY6FTdpABa4)
* [Setting up interface of Jam.py application using Forms Dialogs](https://youtu.be/hvNZ0-a_HHw)


Longer
[video](https://youtu.be/qkJvGlgoabU)  with dashboards and complex internal logic.

Live demos on PythonAnywhere:

- [SAP Theme Demo](https://jampyapp.pythonanywhere.com)
- [Personal Account Ledger from MS Access template](https://msaccess.pythonanywhere.com)

  Below two apps demonstrate Matplotlib, Pandas, NumPy and RFM analysis, which stands for R ecency, F requency, and M onetary value, directly migrated from MS Access template:
  
- [NorthWind Traders from MS Access template V7 DEV (wip)](https://northwind2.pythonanywhere.com)
- [NorthWind Traders from MS Access template V7 (wip)](https://northwind.pythonanywhere.com)

  
- [The ERP POC Demo with Italian and English translations](https://sem.pythonanywhere.com)
- [Assets/Parts Application (wip, currently Jam V7 Demo)](https://jampy.pythonanywhere.com)
- [Machine Learning (wip)](https://mlearning.pythonanywhere.com)
- [Auto Parts Sales for Brazilian Market (Portuguese)](https://carparts.pythonanywhere.com)
- [Resourcing and Billing Application from MS Access DB (wip)](https://resourcingandbilling.pythonanywhere.com)
- [Job Positions tracking App from MS Access DB (wip)](https://positionstracking.pythonanywhere.com)
- [Kanban/Tasks Application, V7](https://kanban.pythonanywhere.com)
- [Assets Inventory Application, V7 (wip)](https://assetinventory.pythonanywhere.com)
- [Google Authentication, V7](https://ipam2.pythonanywhere.com)
- [IP Management V7 (wip)](https://ipmgmt.pythonanywhere.com)
- [Sistema Integrado de Gestão - IMS for Brazilian Market (Portuguese)](https://imsmax.pythonanywhere.com)
- [ Bills of Materials, sourced from  https://github.com/mpkasp/django-bom as no-code,  V7 (wip)](https://billsofmaterials.pythonanywhere.com)


Jam.py alternative site:

https://jampyapplicationbuilder.com/


## Main features

Jam.py is an object oriented, event driven framework with hierarchical structure, modular design
and very tight DB/GUI coupling. The server side of Jam.py is written in [Python](https://www.python.org),
the client utilizes [JavaScript](https://developer.mozilla.org/en/docs/Web/JavaScript),
[jQuery](https://jquery.com) and [Bootstrap](https://getbootstrap.com/docs/5.0/).

* Simple, clear and efficient IDE. The development takes place in the
  Application builder, an application written completely in Jam.py.

* “All in the browser” framework. With Jam.py, all you need are two pages
  in the browser, one for the project, the other for the Application builder.
  Make changes in the Application builder, go to the project, refresh the page,
  and see the results.

* Supports SQLite, PostgreSQL, MySQL, Firebird, MSSQL and
  Oracle databases. The concept of the framework allows you to migrate from
  one database to another without changing the project.

* Authentication, authorization, session management, roles and permissions.

* Automatic creation and modification of database tables and SQL queries generation.

* Data-aware controls.

* Open framework. You can use any Javascript/Python libraries.

* Rich, informative reports. Band-oriented report generation based on
  [LibreOffice](https://www.libreoffice.org) templates.

* Charts. You can use free [jsCharts](http://www.jscharts.com) library
  or any javascript charting library to create charts to represent and analyze your application data.

* Allows to save audit trail/change history made by users

* Predefined css themes.

* Develop and test locally update remotely. Jam.py has Export and Import
  utilities that allow developer to store all metadata (database structures,
  project parameters and code) in a file that can be loaded by another
  application to apply all the changes.

## Documentation


All updated documentation for v7 is online at
https://jampy-docs-v7.readthedocs.io/

Brazilian Portuguese translation started at
https://jampy-docs-v7-br-pt.readthedocs.io/

Please visit https://jampy-docs-v7.readthedocs.io/en/latest/intro/install.html for Python and
framework installation or https://jampy-docs-v7.readthedocs.io/en/latest/intro/new_project.html how to create a
new project.

Jam.py application design tips are at https://jampy-application-design-tips.readthedocs.io/

For general discussion, ideas or similar, please visit mailgroup https://groups.google.com/g/jam-py or
FB page https://www.facebook.com/groups/jam.py/ (paused atm)

## Sponsor

Jam.py is raising funds to keep the software free for everyone, and we need the support of the entire community to do it. [Donate to Jam.py on Github](https://github.com/sponsors/platipusica) to show your support.


## License

Jam.py is licensed under the BSD License.

## Original Author

Andrew Yushev

See also the list of [contributors](http://jam-py.com/contributors.html)
who participated in this project.

## Maintainers

[crnikaurin](https://github.com/crnikaurin), [platipusica](https://github.com/platipusica)

