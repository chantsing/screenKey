#!/usr/bin/env python3
from setuptools import setup
from distutils.command.build import build

class BuildWithCompile(build):
    sub_commands = [('compile_catalog', None)] + build.sub_commands

setup(name='screenkey', version='1.5',
      description='A screencast tool to display keys',

      author='Pablo Seminario',
      author_email='pabluk@gmail.com',
      maintainer='Yuri D\'Elia',
      maintainer_email='wavexx@thregr.org',
      license='GPLv3+',
      keywords='screencast keyboard presentation keys',
      url='http://www.thregr.org/~wavexx/software/screenkey/',

      classifiers=['Development Status :: 5 - Production/Stable',
                   'Environment :: X11 Applications :: GTK',
                   'Intended Audience :: Education',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                   'Operating System :: POSIX',
                   'Operating System :: Unix',
                   'Topic :: Education',
                   'Topic :: Multimedia :: Graphics :: Presentation',
                   'Topic :: Multimedia :: Video :: Capture'],

      long_description="""
      Screenkey is a useful tool for presentations or screencasts.
      Inspired by ScreenFlick and initially based on the key-mon project code.
      """,

      scripts=['screenkey'],
      packages=['Screenkey'],
      setup_requires=['setuptools', 'babel'],
      install_requires=['PyGObject', 'pycairo', 'dbus-python'],
      package_data={'': [
          'images/mouse.svg',
          'locale/*/LC_MESSAGES/screenkey.mo'
      ]},
      data_files=[
          ('share/applications', ['data/screenkey.desktop']),
          ('share/doc/screenkey', ['README.rst', 'NEWS.rst']),
          ('share/metainfo', ['data/org.thregr.screenkey.metainfo.xml'])
      ],
      cmdclass={
          'build': BuildWithCompile,
      },
)
