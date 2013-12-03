from setuptools import setup, find_packages

setup(
    name='django-vkontakte-wall',
    version=__import__('vkontakte_wall').__version__,
    description='Django implementation for vkontakte API Wall',
    long_description=open('README.md').read(),
    author='ramusus',
    author_email='ramusus@gmail.com',
    url='https://github.com/ramusus/django-vkontakte-wall',
    download_url='http://pypi.python.org/pypi/django-vkontakte-wall',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False, # because we're including media that Django needs
    install_requires=[
        'django-vkontakte-api>=0.4.5',
        'django-vkontakte-users>=0.3.6',
        'django-vkontakte-groups>=0.3.8',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
