# Inspired by:
# https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/

import codecs
import os
import re

from setuptools import setup, find_packages


###################################################################

NAME = "webb_scraping"
PACKAGES = find_packages(where=".")
META_PATH = os.path.join("webb_scraping", "__init__.py")
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "Natural Language :: English",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Unix",
    "Operating System :: MacOS",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    'Topic :: Scientific/Engineering :: Astronomy'

]
INSTALL_REQUIRES = ["tqdm", "astropy", "pygments>=2.4.1", "nbsphinx==0.5.1", "nbconvert<6,>=5.5.0", "numpy", "astroquery", "bs4", "requests"]
REQUIRES = ["tqdm", "numpy", "astropy", "pygments>=2.4.1",  "nbsphinx==0.5.1", "nbconvert<6,>=5.5.0", "astroquery", "bs4", "requests"]

###################################################################

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read(META_PATH)


def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE, re.M
    )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))


if __name__ == "__main__":
    setup(
        name=NAME,
        description=find_meta("description"),
        license=find_meta("license"),
        url=find_meta("uri"),
        version=find_meta("version"),
        author=find_meta("author"),
        author_email=find_meta("email"),
        maintainer=find_meta("author"),
        maintainer_email=find_meta("email"),
	    package_data={'': ['README.md', 'LICENSE']},
        long_description=read("README.md"),
        long_description_content_type="text/markdown",
        packages=PACKAGES,
        package_dir={"": "."},
        zip_safe=False,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
        options={"bdist_wheel": {"universal": "1"}},
    )