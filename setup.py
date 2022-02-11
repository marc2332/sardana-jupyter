from setuptools import setup
from os import path

sardana_ipython = path.join(path.dirname(__file__), "sardana_ipython")


setup(
    name="sardana_ipython",
    version="0.1.0",
    packages=["sardana_ipython"],
    package_dir={"sardana_ipython": sardana_ipython},
)
