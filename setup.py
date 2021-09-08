from setuptools import setup


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="gallerist",
    version="0.0.5",
    description="Classes and methods to handle pictures for the web",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    url="https://github.com/Neoteroi/Gallerist",
    author="RobertoPrevato",
    author_email="roberto.prevato@gmail.com",
    keywords="pictures images web",
    license="MIT",
    packages=["gallerist"],
    install_requires=["aiofiles==0.4.0", "Pillow==8.3.2"],
    include_package_data=True,
    zip_safe=False,
)
