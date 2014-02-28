from setuptools import setup


def reqs():
    with open("requirements.txt") as r:
        return list(map(lambda x: x.strip(), r.read().split('\n')))

setup(
    name='django-semantic-mediawiki',
    packages=['django_semantic_mediawiki'],
    version='0.1',
    description='Use the semantic mediawiki API as django models',
    author='Nikita Marchant',
    author_email='nikita.marchant@gmail.com',
    url='https://github.com/C4ptainCrunch/django-semantic-mediawiki',
    download_url='https://github.com/C4ptainCrunch/django-semantic-mediawiki/tarball/0.1',
    keywords=['django', 'mediawiki', 'api', 'manager', 'queryset', 'orm'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2 :: Only',
        'Topic :: Database',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=reqs()
)
