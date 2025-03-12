Un proyecto de [Jorge Luis Endres](mailto://jlecomputer04@gmail.com).

![icon](https://github.com/pieroproietti/pengui/raw/main/assets/pengui.png?raw=true)

# eggsmaker

![eggsmaker-running](/images/eggsmaker-running.png)

`eggsmaker` es una interfaz gráfica para `penguins-eggs`.

Escrito por mi amigo [Jorge Luis Endres](mailto://jlecomputer04@gmail.com), es esencial y funcional. No cubre todas las posibilidades de penguins-eggs, pero al final una GUI debe ser simple e intuitiva.

Me gusta, espero que os guste, y agradezco a Jorge su atrevimiento.

# Development requisites

## Debian

I added only the following packages:

`sudo apt install build-essential`

`sudo apt install python3-pip python3-venv`

Note: Para una configuración sencilla, puedes instalar mi imagen ISO, que también utilizo para el desarrollo de penguins-eggs: [egg-of_debian-bookworm-colibri](https://drive.google.com/drive/folders/18QIqicyecLMuU1Zmb2E039gWawzZuy3e).


## Arch
En Arch `tkinter` no está instalado por defecto y debe ser instalado en el sistema:
```
sudo pacman -S tk
```

Note: Para una configuración sencilla, puedes instalar mi imagen ISO, que también utilizo para el desarrollo de penguins-eggs: [egg-of_arch-colibri](https://drive.google.com/drive/folders/1qWh-hWjldQpb6TWSDY9h8tKdD4VadkOr).

## Openmamba
En Openmamba `tkinter` no está presente por defecto y debe ser instalado en el sistema:
```
sudo dnf install python3-tk python3-devel glibc-devel
```
Note: Para una configuración sencilla, puedes instalar mi imagen ISO, que también utilizo para el desarrollo de penguins-eggs: [egg-of_openmamba-plasma](https://drive.google.com/drive/folders/1-7LbgkKIrp8hUFTbO3qGtPKzaHter6RM).

# Sources
Este es el repositorio de eggsmaker, para obtener estas fuentes: 

`git clone https://github.com/pieroproietti/eggsmaker`

Se recomienda, sin embargo, crear un [fork](https://github.com/pieroproietti/eggsmaker/fork) del repositorio, para que pueda gestionar el proyecto usted mismo y posiblemente crear algunas [Pull Requests](https://github.com/pieroproietti/eggsmaker/pulls).

# Develop
run `bin/create_venv` from the root of the project and and follow the instructions.

Activate virtual environment:
```
source venv_eggsmaker/bin/activate
```

Bajo `bin`, hay scripts útiles para `run`, `create-bin`, `create-deb`, etc. Deben ejecutarse siempre desde la raíz del proyecto y tienes un nombre autoexplicativo.

## Run from sources
`./bin/run`

## Create bin
Estamos usando [nuitka](https://nuitka.net/) en [python](https://www.python.org/). Para crear bin, necesitamos instalar también:

`sudo apt install ccache patchelf`

Para crear el ejecutable:
```
./create-bin
```


# Create packages

## Debian

To create Debian packages we need to install [fpm](https://fpm.readthedocs.io/en/v1.15.1/). 

First install ruby `sudo apt install ruby`, then using gem, install fpm.
```
./bin/create-bin
./bin/create-deb
```
