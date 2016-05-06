#!/usr/bin/env python

if __name__ == '__main__':
    from jam.wsgi import App
    from jam.wsgi_server import run

    application = App()
    run(application)
