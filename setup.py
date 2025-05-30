#!/usr/bin/env python3
from setuptools import setup
import os
from os import walk, path


# TODO update this info!
# Define package information
SKILL_CLAZZ = "TasmotaMQTT"  # Make sure it matches __init__.py class name
VERSION = "0.0.2"
URL = "https://github.com/JoergZ2/ovos-skill-my-tasmota-mqtt"
AUTHOR = "JoergZ2"
EMAIL = ""
LICENSE = "Apache2.0"
DESCRIPTION = "Skill for Tasmota IoT devices controlled by MQTT"

PYPI_NAME = URL.split("/")[-1]  # pip install PYPI_NAME

# Construct entry point for plugin
SKILL_ID = f"{PYPI_NAME.lower()}.{AUTHOR.lower()}"
SKILL_PKG = PYPI_NAME.lower().replace('-', '_')
PLUGIN_ENTRY_POINT = f"{SKILL_ID}={SKILL_PKG}:{SKILL_CLAZZ}"


def get_requirements(requirements_filename: str):
    """
    Parse requirements from a file.

    Args:
        requirements_filename (str, optional): The filename of the requirements file.
            Defaults to "requirements.txt".

    Returns:
        List[str]: A list of parsed requirements.

    Notes:
        If the environment variable MYCROFT_LOOSE_REQUIREMENTS is set, this function
        will modify the parsed requirements to use loose version requirements,
        replacing '==' with '>=' and '~=' with '>='.

    """
    requirements_file = path.join(path.abspath(path.dirname(__file__)),
                                  requirements_filename)
    with open(requirements_file, 'r', encoding='utf-8') as r:
        requirements = r.readlines()
    requirements = [r.strip() for r in requirements if r.strip()
                    and not r.strip().startswith("#")]
    if 'MYCROFT_LOOSE_REQUIREMENTS' in os.environ:
        print('USING LOOSE REQUIREMENTS!')
        requirements = [r.replace('==', '>=').replace('~=', '>=') for r in requirements]
    return requirements


def find_resource_files():
    """ensure all non-code resource files are included in the package"""
    # add any folder with files your skill uses here! 
    resource_base_dirs = ("locale", "ui", "vocab", "dialog", "regex")
    base_dir = path.dirname(__file__)
    package_data = ["*.json"]
    for res in resource_base_dirs:
        if path.isdir(path.join(base_dir, res)):
            for (directory, _, files) in walk(path.join(base_dir, res)):
                if files:
                    package_data.append(
                        path.join(directory.replace(base_dir, "").lstrip('/'),
                                  '*'))
    return package_data


# Setup configuration
setup(
    name=PYPI_NAME,
    version=VERSION,
    description=DESCRIPTION,
    url=URL,
    author=AUTHOR,
    author_email=EMAIL,
    license=LICENSE,
    package_dir={SKILL_PKG: ""},
    package_data={SKILL_PKG: find_resource_files()},
    packages=[SKILL_PKG],
    include_package_data=True,
    install_requires=get_requirements("requirements.txt"),
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
