import os
from setuptools import setup, find_packages
from version import __version__, __app__

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="eggsmaker-web",
    version=__version__,
    author="Jorge Luis Endres",
    description="Graphical interface for Penguins' Eggs ISO creator",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/pieroproietti/penguins-eggs",
    packages=find_packages(),
    py_modules=["main", "backend", "version"],
    include_package_data=True,
    install_requires=requirements,
    data_files=[
        ('share/applications', ['eggsmaker-web.desktop']),
        ('share/pixmaps', ['assets/eggsmaker.png']),
        ('share/eggsmaker-web/assets', ['assets/eggsmaker.png']),
    ],
    scripts=['bin/eggsmaker-web'],
    entry_points={
        "console_scripts": [
            "eggsmaker-web-py=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Installation/Setup",
    ],
    python_requires=">=3.8",
)
