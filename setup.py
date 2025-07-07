from setuptools import setup, find_packages

try:
    with open("requirements.txt") as f:
        requirements = f.read().splitlines()
except FileNotFoundError:
    requirements = []

setup(
    name="watchlist_flows",
    version="0.1",
    packages=find_packages(),
    install_requires=requirements,
)
