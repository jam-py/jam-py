import os
from setuptools import setup
from jam import version

cur_dir = os.getcwd()

setup(
    name='jam.py',
    version=version(),
    url='http://jam-py.com/',
    author='Andrew Yushev',
    author_email='yushevaa@gmail.com',
    description=('Jam.py framework is the fastest way to create a web database application.'),
    license='BSD',
    packages=['jam', 'jam.lang', 'jam.db', 'jam.third_party', 'jam.third_party.werkzeug',
        'jam.third_party.werkzeug.contrib', 'jam.third_party.werkzeug.debug',
        'jam.third_party.slimit', 'jam.third_party.slimit.ply',
        'jam.third_party.slimit.visitors'],
    package_data={'jam': ['admin.html', 'js/*.js', 'js/ace/*.js',
        'img/*.*', 'css/*.*', 'project/*.*', 'project/css/*.*',
        'project/js/*.*', 'project/img/*.*', 'third_party/werkzeug/debug/shared/*.*']},
    scripts=['jam/bin/jam-project.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: JavaScript',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends'
    ],
)
