# python-api-challenge

Pre Req
----------------------
    Docker
    docker-compose


Run
----------------------
    docker-compose up -d

Application will be available on ``localhost:8000`` or ``127.0.0.1:8000`` in your browser.

Web routes
----------

    All routes are available on ``/docs`` or ``/redoc`` paths with Swagger or ReDoc.


Project structure
-----------------

Files related to application are in the ``app`` directory. ``alembic`` is directory with sql migrations.
Application parts are:

::

    models  - pydantic models that used in crud or handlers
    crud    - CRUD for types from models
    db      - db specific utils
    core    - some general components (jwt, security, configuration)
    api     - handlers for routes
    main.py - FastAPI application instance, CORS configuration and api router including
