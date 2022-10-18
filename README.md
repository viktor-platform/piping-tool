# Introduction

Welcome to the Sterke-Lekdijk repo!

Here you can find the code for a tool that performs piping calculations on dykes. This code can be used in a very user friendly way as a [VIKTOR](https://viktor.ai) application, VIKTOR is the low-code platform empowering engineers to build and share user-friendly web apps with nothing but Python.  Running this as a VIKTOR app gives you a user friendly frontend, powerful backend, user administration, version history and much more. However, this code is structured in a way that also allows you to use (parts of) it separately. The actual objects and calculations can be found in the `app` subfolder.

You can find the user manual for this app in the "manual" subfolder, or through a link in the welcome text you see upon entering a VIKTOR workspace (also present in the welcome.md file in this repository).

If you have an interest in this code or want to know more, do not hesitate to contact Roeland Weigand (rweigand@viktor.ai).

# Developing app


This app makes use of code quality tools. These tools are isolated in a seperate requirements file (`dev-requirements.txt`). The following sections helps you with the setup and using these tools.

## Creating a virtual enviroment

To create a venv on Linux:

```
python3 -m venv env
```

Activate the virtual environment:
```
source ./env/bin/activate
```

Install dependencies:
```
pip install -r dev-requirements.txt
```

## Code quality commands
Formatting with black and isort (replace with viktor-cli.exe for Windows):
```
python -m black app/ tests/
python -m isort .
```

Static code analysis:
```
python -m pylint app/ tests/
```

Run tests:
```
viktor-cli test 
```