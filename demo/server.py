#!/usr/bin/env python
print(f"User Guide: https://jampy-docs-v7.readthedocs.io/")
if __name__ == '__main__':
    from jam.wsgi import create_application
    from jam.wsgi_server import run

    application = create_application(__file__)
    run(application)
