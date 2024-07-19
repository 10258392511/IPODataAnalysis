from setuptools import setup, find_packages


setup(
    name="IPODataAnalysis",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scipy",
        "scikit-learn",
        "torch",
        "openpyxl",
        "ipywidgets",
        "tqdm",
        "pymupdf",
        "selenium",
    ]
)
