import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.txt")) as f:
    README = f.read()

requires = [
    "requests",
]

setup(
    name="qozy-client",
    version="0.1",
    description="qozy-client",
    long_description=README,
    author="qozy.io",
    author_email="contact@qozy.io",
    url="https://www.qozy.io",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points={
        "console_scripts": [
            "qozy = qozy_client.cli:main",
        ]
    },
)
