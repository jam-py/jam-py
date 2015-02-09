import os
from distutils.core import setup

cur_dir = os.getcwd()

setup(
    name='jam.py',
    version='1.0.4',
    url='http://jam-py.com/',
    author='Andrew Yushev',
    author_email='yushevaa@gmail.com',
    description=('Jam.py is the fastest way to create a web/desktop database application.'),
    license='BSD',
    packages=['jam', 'jam.lang', 'jam.third_party'],
    install_requires = ['pygtk>=2.24'],
    package_data={'jam': ['ui/*.ui',
        'project/*.*', 'project/web/*.*', 'project/web/contrib/*.*',  'project/web/wsgiserver/*.*',
        'project/js/*.js', 'project/css/*.css', 'project/img/*.*',
        'project/ui/*.*']},
    scripts=['jam/bin/jam-project.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Environment :: X11 Applications :: GTK',
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
