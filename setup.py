from setuptools import setup, find_packages

setup(
    name="ncaa_bbStats",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
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