import os
import sys

import setuptools
import setuptools.command.build_py as orig


try:
    from Cython.Build import cythonize
except ImportError:
    print("You don't seem to have Cython installed. Please get a")
    print("copy from www.cython.org and install it")
    sys.exit(1)


def get_extension_paths(root_dir):
    paths = []
    for root, dirs, files in os.walk(root_dir):
        files = filter(lambda f: f.endswith('.py'), files)
        files = map(lambda f: os.path.join(root, f), files)
        paths.extend(files)
    return paths


# noinspection PyPep8Naming
class build_py(orig.build_py):

    def find_package_modules(self, package, package_dir):
        modules = super().find_package_modules(package, package_dir)
        modules = filter(lambda m: not os.path.exists(m[2].replace('.py', '.c')), modules)
        return modules

    def run(self):
        super().run()


if __name__ == "__main__":
    setuptools.setup(
        name="NES emulator",
        version="0.0.0",
        description="Python NES emulator",
        author="Michał Pstrąg",
        license="MIT",
        packages=['pynes', 'pynes.nes', 'pynes.nes.mappers'],
        package_dir={'pynes': 'src/pynes'},
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent"
        ],
        install_requires=["pygame"],
        python_requires=">=3.8",
        ext_modules=cythonize(get_extension_paths("src"), ["src/pynes/*.py"], language_level="3"),
        cmdclass={
            "build_py": build_py
        }
    )
