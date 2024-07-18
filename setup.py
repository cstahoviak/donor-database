"""
For a discussion of package author vs. deployment author see:
https://stackoverflow.com/questions/14399534/reference-requirements-txt-for-the-install-requires-kwarg-in-setuptools-setup-py

1. The package author writes for a wide variety of scenarios, because they're
putting their work out there to be used in ways they may not know about, and
have no way of knowing what packages will be installed alongside their package.
In order to be a good neighbor and avoid dependency version conflicts with
other packages, they need to specify as wide a range of dependency versions as
can possibly work. This is what install_requires in setup.py does.

2. The deployment author writes for a very different, very specific goal: a
single instance of an installed application or service, installed on a
particular computer.
"""

from setuptools import setup, find_packages

setup(
    name="donordatabase",
    version="2024.0.0",
    description="A custom database for managing donors and payment information.",
    package_dir={"": "src"},
    # packages=find_packages(where="src"),
    # packages=['donordatabase'],
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/cstahoviak/donor-database",
    author="Carl Stahoviak",
    author_email="carlcstahoviak@gmail.com",
    license="MIT",
    install_requires=["pandas",
                      "pyqt6",
                      "matplotlib",
                      "numpy"],
    python_requires=">=3.8"
)
