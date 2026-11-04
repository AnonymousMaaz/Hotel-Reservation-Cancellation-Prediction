from setuptools import setup, find_packages
import os


def get_requirements(file_path: str):
    """Parses the requirements.txt file and returns the requirements list."""
    with open(file_path) as f:
        requirements = f.read().splitlines()

    return requirements


if __name__ == "__main__":
    requirements = get_requirements("requirements.txt")
    setup(
        name="Hotel Reservation",
        version="0.1.0",
        author="Maaz Khan",
        packages=find_packages(),
        install_requires=requirements,
    )
