from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='gallerist',
      version='0.0.1',
      description='Classes and methods to handle pictures for the web',
      long_description=readme(),
      long_description_content_type='text/markdown',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Operating System :: OS Independent'
      ],
      url='https://github.com/RobertoPrevato/Gallerist',
      author='RobertoPrevato',
      author_email='roberto.prevato@gmail.com',
      keywords='pictures images web',
      license='MIT',
      packages=['gallerist'],
      install_requires=[],
      include_package_data=True,
      zip_safe=False)
