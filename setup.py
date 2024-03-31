from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_bytes().decode("utf-8")

VERSION = "0.1.2"
DESCRIPTION = "An ECS game engine library created with SDL2 and Python."
LONG_DESCRIPTION = long_description

# Setting up

setup(
    name="arepy",
    version=VERSION,
    author="Scr44gr",
    author_email="<scr44gr@protonmail.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "PyGLM",
        "pysdl2",
        "pysdl2-dll",
        "bitarray",
        "python-dotenv",
        "pillow",
        "numpy",
        "freetype-py",
        "PyOpenGL",
    ],
    extras_require={"imgui": ["imgui"]},
    keywords=["ecs", "game-engine", "sdl2-wrapper", "python-game-engine"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.10",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
