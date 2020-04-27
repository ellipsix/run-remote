import setuptools

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='run-remote',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    author='David Zaslavsky',
    author_email='diazona@ellipsix.net',
    description='Small utility to run programs from one host on another',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities'
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'run-remote = run_remote.__main__:main'
        ]
    }
)
