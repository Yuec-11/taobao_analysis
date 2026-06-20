#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
淘宝用户行为数据分析 - 项目安装脚本
"""

from setuptools import setup, find_packages

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

with open('requirements.txt', encoding='utf-8') as f:
    requirements = [line.strip() for line in f
                    if line.strip() and not line.startswith('#') and not line.startswith('sqlite3')]

setup(
    name='taobao-user-behavior-analysis',
    version='1.0.0',
    description='淘宝用户行为数据分析 - 清洗、分析、可视化、RFM用户价值分群',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Data Analysis Team',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    entry_points={
        'console_scripts': [
            'taobao-analysis=main:main',
        ],
    },
)
