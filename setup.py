import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="shell-command-management",
    version="0.0a1-dev1",
    author="Václav Blažej",
    author_email="vaclavblazej@seznam.cz",
    description="Tool for managing custom commands from a central location",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vaclavblazej/command",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Topic :: Utilities",
    ],
    python_requires='>=3.8',
    entry_points={
            "console_scripts": [
                "cmd = cmd.__main__:main",
            ]
        }
)
