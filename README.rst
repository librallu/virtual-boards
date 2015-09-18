PROJECT UNDER DEVELOPMENT
=========================

Overview
========

*Virtual Boards* application represents boards containing columns that contains notes.

Notes can represent a shopping list, a project management board, ...






installation
============

get the source : 

.. code:: bash

    git clone URL



install virtualenv

.. code:: bash

    pip install virtualenv --user


launch virtualenv

.. code:: bash

    source venv/bin/activate


install flask and other external flask modules

.. code:: bash

    pip install flask flask-script flask-sqlalchemy flask-migrate flask-restful

run python command

.. code:: bash

    python main.py runserver



create database
---------------

.. code:: bash

    python main.py db init

.. code:: bash

    python main.py db migrate
    
.. code:: bash

    python main.py db upgrade




REST API Documentation
======================

For all requests, the default output format is a HTML page.
It is possible to ask a JSON output by adding a *get* parameter
with name *type* and value *json*.

Example :

.. parsed-literal::
    
    http://host:port/v1/?type=json

output :

.. parsed-literal::

    {
      "board-interactions": [...],
      "boards": [...],
      "column-interactions": [...],
      "columns": [...],
      "notes": [...]
    }

In some cases (i.e. HTML forms), PUT and DELETE methods are not allowed.
To cope with this limitation, it is possible to define in the POST request
an optional field with name *request-type* with values *delete*, *put*
to use DELETE and PUT methods instead.




GET all the boards
------------------

 - URL: http://host:port/v1/boards/
 - request method: GET
 - parameters : None
 
 Usage Example: 
 
 .. parsed-literal::
 
    curl <ROOT URL>/v1/boards/?type=json
 


ADD a board
-----------

 - URL: http://host:port/v1/boards/
 - request method: POST
 - parameters :
    - name: (string) name of the board

exemple:

.. parsed-literal::

    curl -X POST <HOST>/v1/boards/ --data "name=new-board"
    {"code": 201, "description": "created"}



ADD a column
------------

 - URL: http://host:port/v1/columns/
 - request method: POST
 - parameters :
    - name: (string) name of the column

exemple:

.. parsed-literal::

    curl -X POST <HOST>/v1/columns/ --data "name=new-column"
    {"code": 201, "description": "created"}

    

ADD a note
----------

 - URL: http://host:port/v1/notes/
 - request method: POST
 - parameters :
    - name: (string) name of the note
    - content: (string) content of the note


usage example:

.. parsed-literal::

    curl <HOST>/v1/notes/ -X POST --data "name=test&text=description"

output:

.. parsed-literal::
    
    {
        "code": 201, 
        "description": "created"
    }

    

DELETE a board
--------------

- URL: http://host:port/v1/boards/
- request method: DELETE

example:

.. parsed-literal::

    curl -X DELETE <HOST>/v1/boards/ --data "id=2"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}



DELETE a column
---------------

- URL: http://host:port/v1/columns/<COLUMN-ID>
- request method: DELETE


example:

.. parsed-literal::

    curl -X DELETE <HOST>/v1/columns/ --data "id=2"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}


DELETE a note
-------------

- URL: http://host:port/v1/notes/<NOTE-ID>
- request method: DELETE

example:

.. parsed-literal::

    curl -X DELETE <HOST>/v1/notes/ --data "id=2"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}


MODIFY a board
--------------

- URL: http://host:port/v1/boards/<BOARD-ID>
- request method: PUT
- optional parameters :
    - name: (string) name of the board
    
example:

.. parsed-literal::

    curl -X DELETE <HOST>/v1/boards/ --data "id=2&name=modified_name"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}


MODIFY a column
---------------

- URL: http://host:port/v1/columns/<COLUMN-ID>
- request method: PUT
- optional parameters :
    - name: (string) name of the column
    
example:

.. parsed-literal::

    curl -X DELETE <HOST>/v1/columns/ --data "id=2&name=modified_name"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}


MODIFY a note
-------------

- URL: http://host:port/v1/notes/<NOTE-ID>
- request method: PUT
- optional parameters :
    - name: (string) name of the note
    - content: (string) content of the note

.. parsed-literal::

    curl -X DELETE <HOST>/v1/notes/ --data "id=2&name=modified_name"
    {"code": 204, "description": "No content: The request was processed successfully, but no response body is needed."}


ADD a column in a board
-----------------------

- URL: http://host:port/v1/boards-content/
- request method: POST
- parameters:
    - board-id: id of the board
    - column-id: id of the column


ADD a note in a column
----------------------

- URL: http://host:port/v1/columns-content/
- request method: POST
- parameters:
    - column-id: id of the column
    - note-id: id of the note


DELETE a column in a board
--------------------------

- URL: http://host:port/v1/boards-content/
- request method: DELETE
- parameters:
    - board-id: id of the board
    - column-id: id of the column
    

DELETE a note in a column
-------------------------

- URL: http://host:port/v1/columns-content/
- request method: DELETE
- parameters:
    - column-id: id of the column
    - note-id: id of the note


TODO list
=========

- integrate in the documentation CURL calls
- make html5+js client with polymer
- prototype of droppelganger drag and drop library for mobiles (can be simple in the first version)
