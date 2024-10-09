import importlib.util
import os
from setuptools import setup
import sys


# Function to dynamically load the module and get its version
module_name = 'version'
module_path = os.path.join(os.path.dirname(__file__), 'src', 'libcrawler', 'version.py')

def get_version():
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module.__version__

# Read the requirements from requirements.txt
def read_requirements():
    with open('requirements.txt') as req:
        content = req.readlines()
    # Remove comments and empty lines
    requirements = [line.strip() for line in content if line.strip() and not line.startswith('#')]
    return requirements

setup(
    version=get_version(),
    install_requires=read_requirements(),
)