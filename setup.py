# -*- coding: utf-8 -*-
from distutils.core import setup
LONGDOC = """
A pure python sdk for XuperChain
"""

setup(name='xuper',
      version='0.02',
      description='Pure Python SDK for XuperChain',
      long_description=LONGDOC,
      author='Sun, Junyi',
      author_email='ccnusjy@gmail.com',
      url='https://github.com/xuperchain/xuperunion',
      license="MIT",
      classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: Chinese (Traditional)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      ],
      install_requires=[
        "requests",
        "ecdsa",
      ],
      keywords='Blockchain,XuperChain,Smart Contract',
      packages=['xuper'],
      package_dir={'xuper':'xuper'},
      package_data={'xuper':['*.*']}
)
