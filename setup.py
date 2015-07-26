from setuptools import setup

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
LICENSE = open('LICENSE.txt').read()

setup(
    name='natcap.testing',
    description="Software testing for natcap projects",
    long_description=readme + '\n\n' + history,
    maintainer='James Douglass',
    maintainer_email='jdouglass@stanford.edu',
    url='https://bitbucket.org/jdouglass/natcap.testing',
    namespace_packages=['natcap'],
    install_requires=[
        'gdal'
    ],
    packages=[
        'natcap',
        'natcap.testing',
    ],
    version='0.0.1',
    license=LICENSE,
    zip_safe=False,
    keywords='natcap testing',
    classifiers=[
        'Intended Audience :: Developers',
        'Development Status :: 2 - Pre-Alpha',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2 :: Only',
    ]
)
