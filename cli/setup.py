"""
SalesAgent CLI - Setup Script

Install with:
    pip install -e .

Then use:
    salesagent --help
"""

from setuptools import setup, find_packages

setup(
    name='salesagent-cli',
    version='1.0.0',
    description='🚀 SalesAgent CLI - AI-Powered Sales Outreach from Your Terminal',
    author='Shailesh',
    author_email='shailesh@salesagentai.com',
    py_modules=['salesagent'],
    install_requires=[
        'requests>=2.28.0',
        'colorama>=0.4.6',
    ],
    entry_points={
        'console_scripts': [
            'salesagent=salesagent:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Office/Business',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
