# -*- coding: utf-8 -*-


from setuptools import setup


VERSION = '0.1'


setup(
    name='pylane',
    version=VERSION,
    author='valensc, Wu Xiao',
    author_email='weidong1312@gmail.com, None',
    url='https://github.com/NtesEyes/pylane',
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
        "ipython>=4.0.0"
    ],
    keywords=['debug', 'attach', 'gdb', 'shell']
)
