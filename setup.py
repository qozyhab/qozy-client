import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    "requests",
]

tests_require = [
]

setup(name='qozy-client',
      version='0.0',
      description='qozy-client',
      long_description=README + '\n\n' + CHANGES,
      author='',
      author_email='',
      url='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      entry_points={
          "console_scripts": [
              "qozy = qozy_client.cli:main",
          ]
      },
      )
