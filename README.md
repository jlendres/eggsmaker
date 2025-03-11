# eggsmaker

A project from [Jorge Luis Endres](mailto://jlecomputer04@gmail.com).

![icon](https://github.com/pieroproietti/pengui/raw/main/assets/pengui.png?raw=true)

`eggsmaker` è una GUI per `penguins-eggs`.
Scritto dall'amico [Jorge Luis Endres](mailto://jlecomputer04@gmail.com), è essenziale e funzionale. Non copre tutta le possibilità di eggs ma alla fine una GUI deve essere semplice ed intuibile.

A me piace, spero piaccia a voi e ringrazio Jorge per il suo cimento.

![eggsmaker-running](/images/eggsmaker-running.png)

# Development requisites

## Debian

I added only the following packages:

`sudo apt install build-essential`

`sudo apt install python3-pip python3-venv`

Note: just install my `egg-of_debian-bookworm-colibri`.


## Arch
Su Arch tkinter non è installato di default e va installato nel sistema:
```
sudo pacman -S tk
```

## Openmamba
Su Openmamba `tkinter` non è presente di default e va installato nel sistema:
```
sudo dnf install python3-tk python3-devel glibc-devel
```

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

# Packages

## Debian

To create Debian packages we need to install [fpm](https://fpm.readthedocs.io/en/v1.15.1/). 

First install ruby `sudo apt install ruby`, then with gem, install fpm.
```
./bin/create-bin
./bin/create-deb
```
