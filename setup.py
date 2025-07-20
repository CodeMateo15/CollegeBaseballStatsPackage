from setuptools import setup, find_packages

setup(
    name="src",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["pandas"],
    include_package_data=True,
    package_data={
        "teamstats": [
            "data/div1/*.json",
            "data/div2/*.json",
            "data/div3/*.json",
        ]
    },

)