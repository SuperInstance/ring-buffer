from setuptools import setup, find_packages

setup(
    name="ring-buffer",
    version="0.1.0",
    description="Audio pipeline NaN guard — fixed-length ring buffer with sanitisation",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="SuperInstance",
    url="https://github.com/SuperInstance/ring-buffer",
    packages=find_packages(),
    python_requires=">=3.9",
    extras_require={
        "numpy": ["numpy>=1.20"],
        "test": ["pytest>=7.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    license="MIT",
)
