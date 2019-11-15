# -*- coding: utf-8 -*-


from setuptools import setup
from os import path


VERSION = '0.0.9'

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()


setup(
    name='pylane',
    version=VERSION,
    author='valensc, Wu Xiao',
    author_email='weidong1312@gmail.com, notgiven@gmail.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/NtesEyes/pylane',
    download_url='https://github.com/NtesEyes/pylane/archive/0.0.2.tar.gz',
    packages=[
        'pylane',
        'pylane.core',
        'pylane.shell',
    ],
    entry_points="""
          [console_scripts]
          pylane = pylane.entry:main
      """,
    # cmdclass={
        # 'build_py': build_py
    # },
    install_requires=[
        "ipython==5.7",
        # 'ipython==5.8;python_version<"3.4"',
        # 'ipython==7.2;python_version>="3.4"',
        "Click==7.0",
    ],
    keywords=['debug', 'attach', 'gdb', 'shell']
)
