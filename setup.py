import os
from setuptools import setup

cur_dir = os.getcwd()

setup(
    name='jam.py',
    version='2.0.3',
    url='http://jam-py.com/',
    author='Andrew Yushev',
    author_email='yushevaa@gmail.com',
    description=('Jam.py is the fastest way to create a web database application.'),
    license='BSD',
    packages=['jam', 'jam.lang', 'jam.third_party', 'jam.third_party.web',
        'jam.third_party.web.contrib', 'jam.third_party.web.wsgiserver',
        'jam.third_party.slimit', 'jam.third_party.slimit.ply',
        'jam.third_party.slimit.visitors'],
    package_data={'jam': ['project/*.*', 'project/js/*.js', 'project/js/ace/*.js',
        'project/css/*.css', 'project/img/*.*']},
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
