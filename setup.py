from setuptools import setup, find_packages

setup(
    name="bnxconvertidor",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pyspark"
    ],
    entry_points={
        "console_scripts": [
            "etl-migrate=migrator.main:main"
        ]
    }
)
