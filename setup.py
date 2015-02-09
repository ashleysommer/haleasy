__author__ = 'Matt Clark'

with open('README.rst') as f:
    long_desc = f.read()

from setuptools import setup
setup(
    name = "HALEasy",
    version = "0.2.2",
    py_modules = ['haleasy'],

    # metadata for upload to PyPI
    author = "Matt Clark",
    author_email = "matt@mattclark.net",
    description = "A HAL client which is very short and simple",
    long_description = long_desc,
    license = "MIT",
    keywords = ['HAL','json', 'hypermedia', 'client'],
    classifiers = ['Programming Language :: Python',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   'License :: OSI Approved :: MIT License',
                   'Intended Audience :: Developers',
                   'Development Status :: 5 - Production/Stable',
                   'Operating System :: OS Independent'],
    url = "http://github.com/mattclarkdotnet/haleasy",
    install_requires = [
        'dougrain>=0.5.1',
        'requests>=2.5.1',
        'uritemplate>=0.6',
    ]

)
