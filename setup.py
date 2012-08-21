#!/usr/bin/env python

from distutils.core import setup
setup(name='Nimble WSGI Daemon',
      version='0.4alpha2',
      author = "Keentap",
      author_email = "keentap@gmail.com",
      packages=['nimble', 'nimble.client', 'nimble.protocols', 'nimble.server'])
