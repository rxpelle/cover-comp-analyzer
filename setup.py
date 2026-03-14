from setuptools import setup, find_packages

setup(
    name='cover-comp-analyzer',
    version='0.1.0',
    description='Analyze your book cover against genre competitors using AI vision',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Randy Pellegrini',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'click>=8.0',
        'rich>=13.0',
        'python-dotenv>=1.0',
        'anthropic>=0.18',
        'Pillow>=10.0',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
        ],
    },
    entry_points={
        'console_scripts': [
            'cover-comp-analyzer=cover_comp_analyzer.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
