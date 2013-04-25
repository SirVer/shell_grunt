from distutils.core import setup
import os

setup(
        name = 'shell_grunt',
        version = '1.0',
        url = 'https://github.com/sirver/shell_grunt',
        author = 'Holger "SirVer" Rapp',
        author_email = 'sirver@gmx.de',
        description = "A simple executor framework for running shell commands on file system events.",
        long_description = """\
This is is a thin wrapper around watchdog, but does not use a DSL, but python for configuration.
  """,
  classifiers = [
      "Development Status :: 5 - Production/Stable",
      "License :: OSI Approved :: GPLv3",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Programming Language :: Python :: 2",
      "Programming Language :: Cython",
      ],
  install_requires=[
      'watchdog >= 0.6.0',
      'colorama >= 0.2.5'
  ],
  py_modules = [
      'shell_grunt',
  ],
)

