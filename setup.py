from setuptools import setup

if __name__ == "__main__":
    setup(
        name="NES emulator",
        description=" NES emulator written in Python",
        author="Michał Pstrąg",
        license="MIT",
        license_file="LICENSE.md",
        packages = ["nes"],
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License"
        ],
        install_requires=["numpy"],
        python_requires=">=3.7",
        extras_require={
            "testing": ["pytest", "mypy"]
        }
    )