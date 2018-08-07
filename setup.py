#!/usr/bin/env python

from setuptools import setup


setup(name='sqllib',
      version='0.1',
      description='SQL Templates for Python',
      long_description=open("README.md", "r").read(),
      author='Mike Steder',
      author_email='steder@gmail.com',
      url='http://github.com/steder/sqllib',
      modules=["sqllib.py"],
      test_suite="test_sqllib",
      install_requires=[],
      license="MIT",
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7'
          ]
)
