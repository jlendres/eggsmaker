# eggsmaker

A project from [Jorge Luis Endres](mailto://jlecomputer04@gmail.com).


![icon](https://github.com/pieroproietti/pengui/raw/main/assets/pengui.png?raw=true)

# Development prerequisites Debian bookworm

I added only the following packages:

`sudo apt install build-essential`

`sudo apt install python3-pip python3-venv`

Note: just install my `egg-of_debian-bookworm-colibri`.

# Sources
This is the repository of eggsmaker, to get this sources just: 

`git clone https://github.com/pieroproietti/eggsmaker

It is recommended, however to create yourself a [fork](https://github.com/pieroproietti/eggsmaker/fork) of the repository, so that you can manage the project yourself and possibly create some [Pull Requests](https://github.com/pieroproietti/eggsmaker/pulls).


# start to develop
run `bin/create_venv` from the root of the project and and follow the instructions.

Activate virtual environment:
```
source venv_eggsmaker/bin/activate
```

Under `bin`, there are usefull scripts to `run`, `create-bin`, `create-deb`, etc. They must always be run from the root of the project and have a self-explanatory name.

## Runnint it
`./bin/run`

## Create bin
We are using [nuitka](https://nuitka.net/) **2.1.5** on [python](https://www.python.org/) **3.11.2**. To create bin, we need to install too:

`sudo apt install ccache patchelf`

## Create Debian packages
To create Debian packages we need to install [fpm](https://fpm.readthedocs.io/en/v1.15.1/). 

First install ruby `sudo apt install ruby`, then with gem, install fpm.
