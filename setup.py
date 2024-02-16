from setuptools import setup, find_packages

setup(
    name='autoOpenFoam',
    version='0.0.4',
    packages=find_packages(),
    description='eine kleine automatisirung für openfoam',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Falk mit gpt',
    url='https://github.com/quojus/autoOpenFoam',
        install_requires=[
        'numpy'
    ],
    python_requires='>=3.8',
)
