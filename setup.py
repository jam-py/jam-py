import os
from setuptools import setup
from jam import version

setup(
    name='jam.py',
    version=version(),
    url='http://jam-py.com/',
    author='Andrew Yushev',
    author_email='andrew@jam-py.com',
    description=('Jam.py is an event-driven framework for the development of web database applications.'),
    license='BSD',
    packages=['jam', 'jam.db', 'jam.third_party', 'jam.third_party.werkzeug',
        'jam.third_party.werkzeug.contrib', 'jam.third_party.werkzeug.debug',
        'jam.third_party.pyjsparser'],
    package_data={'jam': ['builder.html', 'langs.sqlite', 'js/*.js',
        'js/ace/*.js', 'img/*.*', 'css/*.*', 'project/*.*', 'project/css/*.*',
        'third_party/werkzeug/debug/shared/*.*']},
    scripts=['jam/bin/jam-project.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends'
    ],
)
