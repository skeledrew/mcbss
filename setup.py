from os.path import join, dirname
from setuptools import setup

def read_text(fname):
    return open(join(dirname(__file__), fname)).read()

setup(
    name = 'mycroftbss',
    version = '0.0.2',
    author = 'Andrew Phillips',
    author_email = 'skeledrew@gmail.com',
    description = ('An extension of the Mycroft brain-skill to aid communication with other skills'),
    license = 'AGPLv3',
    keywords = 'mycroft brain-skill',
    url = 'https://github.com/skeledrew/mcbss',
    packages = ['mycroftbss'],
    long_description = read_text('README.md'),
    classifiers = [
        'Topic :: Utilities'
    ]
)
