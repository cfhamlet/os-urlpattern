from setuptools import find_packages, setup


def read(*filenames, **kwargs):
    import io
    from os.path import join, dirname
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(join(dirname(__file__), filename), encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


setup(
    name='os-urlpattern',
    version=read('src/os_urlpattern/VERSION'),
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    license='MIT License',
    description='Cluster url pattern automatically.',
    long_description=open('README.rst').read(),
    author='Ozzy',
    author_email='cfhamlet@gmail.com',
    url='https://github.com/cfhamlet/os-urlpattern',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'pattern-make = os_urlpattern.cmdline:make',
            'pattern-match = os_urlpattern.cmdline:match',
        ]
    },
    extras_require={'memory': ['psutil'], 'ete_tree': ['six', 'ete3']},
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ])
