# Fase 0 Preparación del proyecto

## Objetivo

Preparar un entorno independiente para desarrollar y ejecutar
Dashboard 360 con Python.

## Ubicación de trabajo

El proyecto se desarrolla dentro de Dashboard360.

Los nueve CSV originales están en data/raw y se conservan
sin modificaciones.

## Terminal utilizada

Bash de MSYS2 UCRT64 en Windows.

Los comandos Get-Location y Get-ChildItem pertenecen a PowerShell.
En esta terminal utilizamos pwd y ls.

## 1 Comprobar la ubicación

```bash
pwd
```

Muestra la carpeta actual. Debe terminar en Dashboard360
o dashboard360.

```bash
ls -la
```

Lista archivos y carpetas, incluyendo los ocultos.

```bash
ls data/raw
```

Permite comprobar los archivos de entrada.

## 2 Elegir Python

```bash
py -3.12 --version
```

Versión comprobada: Python 3.12.9.

Inicialmente se creó un entorno con Python 3.14.
Se decidió utilizar Python 3.12 para este proyecto.

## 3 Reemplazar el entorno inicial

Se desactivó el entorno anterior:

```bash
deactivate
```

Se conservó temporalmente con otro nombre:

```bash
mv .venv .venv-python314-respaldo
```

Se creó el entorno definitivo:

```bash
py -3.12 -m venv .venv
```

Un entorno virtual mantiene las dependencias del proyecto
separadas de las de otros proyectos y del Python general.

Los comandos anteriores registran una acción ya realizada.
No deben repetirse cada vez que se abre la terminal.

## 4 Activar el entorno

Desde Dashboard360:

```bash
source .venv/Scripts/activate
```

La terminal muestra (.venv) cuando está activado.

Este paso se repite al abrir una terminal nueva, si el entorno
no se activa automáticamente.

Para comprobar el intérprete:

```bash
python --version
```

```bash
python -c "import sys; print(sys.executable)"
```

El ejecutable debe estar dentro de Dashboard360/.venv.

## 5 Instalar las dependencias iniciales

```bash
python -m pip install pandas pytest
```

- pandas permite leer y transformar tablas.
- pytest permite ejecutar pruebas automatizadas.
- python -m pip utiliza el instalador del Python seleccionado.

Las bibliotecas instaladas en el Python general no se comparten
automáticamente con el entorno virtual.

## 6 Comprobar las bibliotecas

```bash
python -c "import pandas; import pytest; print('pandas:', pandas.__version__); print('pytest:', pytest.__version__)"
```

Las importaciones deben terminar sin errores y mostrar versiones.

## 7 Registrar las dependencias

```bash
python -m pip freeze > requirements.txt
```

pip freeze lista las versiones instaladas.
El símbolo > guarda esa salida en el archivo y reemplaza
su contenido si ya existía.

```bash
cat requirements.txt
```

Muestra el contenido guardado.

Para instalar estas versiones en un entorno nuevo:

```bash
python -m pip install -r requirements.txt
```

Crear requirements.txt registra las dependencias.
Instalar con -r utiliza ese registro.

## 8 Crear la estructura

```bash
mkdir -p data/processed docs reports src tests
```

Crea las carpetas ausentes y conserva las existentes.

```bash
ls -d data/raw data/processed docs reports src tests
```

Comprueba que las rutas están disponibles.

## 9 Crear y comprobar .gitignore

Paso realizado por el estudiante y comprobado en disco por Codex.
El archivo está en `Dashboard360/.gitignore`.

Desde Bash se entró al proyecto:

```bash
cd /c/Users/favio/ProyectoDiplimadoPython/Dashboard360
```

Se creó el archivo con el siguiente bloque completo:

```bash
cat > .gitignore <<'EOF'
# Entornos virtuales
.venv/
.venv-python314-respaldo/

# Archivos temporales de Python
__pycache__/
*.py[cod]

# Cache de pruebas
.pytest_cache/

# Secretos locales
.env

# Resultados generados
data/processed/*
reports/*
EOF
```

`cat` recibe el texto hasta `EOF`. La redirección `>` lo guarda en
`.gitignore` y reemplaza su contenido si ya existía. Este comando ya
fue ejecutado; no es necesario repetirlo.

Las reglas indican a Git qué archivos omitir al incorporar archivos
nuevos al historial. No borran archivos, no cambian el entorno Python
y no retiran automáticamente archivos que Git ya estuviera siguiendo.

La comprobación realizada fue:

```bash
cat .gitignore
```

Resultado: la terminal mostró las reglas completas y Codex comprobó
que coinciden con el contenido guardado en disco.

## Problemas encontrados

### Comandos de PowerShell en Bash

Síntoma: command not found.

Solución: utilizar los comandos correspondientes a Bash.

### pandas ausente en el entorno

Síntoma: ModuleNotFoundError.

Causa: la biblioteca no estaba instalada en el intérprete utilizado.

Solución: instalar las dependencias dentro del entorno del proyecto.

### Caracteres extra al pegar un comando

Se intentó ejecutar `[200~ls -la .gitignore~` y Bash respondió
`command not found`. El texto pegado contenía caracteres extra.
El comando correcto es `ls -la .gitignore`.
La comprobación posterior con `cat .gitignore` funcionó, por lo que
no es necesario repetir la creación del archivo.

## 10 Completar la instalación y verificar el entorno

Fecha: 26 de octubre de 2026.

Tras detectar que pandas y pytest no estaban disponibles en el entorno
actual, el estudiante pidió a Codex completar la solución. La instalación
manual anterior había terminado con `Operation cancelled by user`.

Codex instaló las versiones existentes en `requirements.txt` directamente
en `.venv`. No se cambió el contenido de `requirements.txt`.
El primer intento restringido falló; el reintento autorizado terminó
correctamente con `Successfully installed`.

Comando ejecutado por Codex en PowerShell desde Dashboard360:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Comando equivalente para estudiar o reproducir desde Bash UCRT64:

```bash
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Este paso ya está completado; no es necesario repetir la instalación.
Se utiliza la ruta explícita al ejecutable para seleccionar el entorno
correcto, independientemente de si está activado en la terminal.

Se ejecutaron las siguientes comprobaciones con el Python de `.venv`.
Los comandos se muestran aquí en su forma equivalente para Bash:

```bash
./.venv/Scripts/python.exe -c "import sys,pandas,pytest; print('Python:',sys.version.split()[0]); print('Ejecutable:',sys.executable); print('pandas:',pandas.__version__); print('pytest:',pytest.__version__)"
```

```bash
./.venv/Scripts/python.exe -m pip check
```

`pip check` comprueba la compatibilidad de las dependencias instaladas;
no sustituye las futuras pruebas del código del proyecto.

## Evidencias

Resultados comprobados por Codex tras completar la instalación:

```text
Python: 3.12.9
Ejecutable: C:\Users\favio\ProyectoDiplimadoPython\Dashboard360\.venv\Scripts\python.exe
pandas: 3.1.0
pytest: 9.1.1
No broken requirements found.
```

- `.gitignore` existe y contiene las reglas verificadas.
- `requirements.txt` existe y se utilizó sin modificar sus versiones.
- Se comparó el contenido de los nueve CSV con `olist_raw.zip` del
  repositorio local del curso mediante SHA-256: todos coinciden.
- Las carpetas `data/processed`, `docs`, `reports`, `src` y `tests`
  estaban presentes en la revisión del proyecto.

## Estado

Preparación técnica del entorno completada y comprobada.
Al cerrar la preparación todavía no se había desarrollado código del pipeline.
En una revisión anterior no se encontró la guía Word. En la revisión
actual se encontró y se leyó `docs/Guia_desarrollo_Dashboard_360_Olist.docx`.

La preparación fue completada antes de crear el primer script.
El avance posterior se registra en `02_exploracion.md`.
