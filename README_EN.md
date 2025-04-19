# eggsmaker

### A project by [Jorge Luis Endres](mailto://jlecomputer04@gmail.com).

![eggsmaker-running](/images/eggsmaker-running.png)

eggsmaker is a graphical interface for penguins-eggs.

Written by my friend [Jorge Luis Endres](mailto://jlecomputer04@gmail.com), it is essential and functional. It doesn’t cover all the possibilities of penguins-eggs, but in the end, a GUI should be simple and intuitive.

I like it, I hope you like it too, and I thank Jorge for his daring.

# Development requisites

## Debian

I’ve only added the following packages:

sudo apt install build-essential

sudo apt install python3-pip python3-venv

Note: For a simple setup, you can install my ISO image, which I also use for penguins-eggs development: [egg-of_debian-bookworm-colibri](https://drive.google.com/drive/folders/18QIqicyecLMuU1Zmb2E039gWawzZuy3e).

## Arch
On Arch, tkinter is not installed by default and must be installed on the system:
sudo pacman -S tk

Note: For a simple setup, you can install my ISO image, which I also use for penguins-eggs development: [egg-of_arch-colibri](https://drive.google.com/drive/folders/1qWh-hWjldQpb6TWSDY9h8tKdD4VadkOr).

## Openmamba
On Openmamba, tkinter is not present by default and must be installed on the system:
sudo dnf install python3-tk python3-devel glibc-devel

Note: For a simple setup, you can install my ISO image, which I also use for penguins-eggs development: [egg-of_openmamba-plasma](https://drive.google.com/drive/folders/1-7LbgkKIrp8hUFTbO3qGtPKzaHter6RM).

# Sources
This is the repository for eggsmaker, to get these sources:

git clone https://github.com/pieroproietti/eggsmaker

However, it is recommended to create a [fork](https://github.com/pieroproietti/eggsmaker/fork) of the repository, so you can manage the project yourself and possibly create some [Pull Requests](https://github.com/pieroproietti/eggsmaker/pulls).

# Develop
run bin/create_venv from the root of the project and follow the instructions.

Activate virtual environment:
source venv_eggsmaker/bin/activate

Under bin, there are useful scripts for run, create-bin, create-deb, etc. They should always be executed from the root of the project and have self-explanatory names.

## Run from sources
./bin/run

## Create bin
We are using [nuitka](https://nuitka.net/) in [python](https://www.python.org/). To create bin, we also need to install:

sudo apt install ccache patchelf

To create the executable:
./create-bin

# Create packages

## Debian
To create Debian packages, we need to install [fpm](https://fpm.readthedocs.io/en/v1.15.1/).

First, install ruby sudo apt install ruby, then using gem, install fpm.

Create the executable, then create the deb package:

./bin/create-bin
./bin/create-deb

# installation
Currently, I’ve only created the package for Debian bookworm, which you can find in the penguins-eggs-ppa repository and install with sudo apt install eggsmaker.
