#!/usr/bin/env python3
"""Setup configuration for FAIRBio CLI tools."""

from setuptools import setup, find_packages
import os

# Read the README
readme_file = os.path.join(os.path.dirname(__file__), "README.md")
long_description = ""
if os.path.exists(readme_file):
    with open(readme_file, 'r') as f:
        long_description = f.read()

setup(
    name="fairbio",
    version="0.1.0",
    description="LLM agents for FAIR reproducibility assessment in scientific research",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="FAIRBio Contributors",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "fairbio-ga4gh-registry=fairbio.cli.find_ga4gh:main",
            "fairbio-trs=fairbio.cli.find_trs:main",
        ],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering",
    ],
)
