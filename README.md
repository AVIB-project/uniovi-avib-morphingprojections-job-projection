[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# Description

> Uniovi AVIB Morphing Projection Job.

## Scaffolding your python project:

```
$ putup --markdown uniovi-avib-morphingprojections-job-projection -p morphingprojections_job_projection \
      -d "Uniovi AVIB Morphing Projection Job Projection." \
      -u https://dev.azure.com/gsdpi/avib/_git/uniovi-avib-morphingprojections-job-projection
```

Create a virtual environment in you python project and activated it:

```
$ cd uniovi-avib-morphingprojections-job-projection

$ python3 -m venv .venv 

$ source .venv/bin/activate
(.venv) miguel@miguel-Inspiron-5502:~/git/uniovi/uniovi-avib-morphingprojections-job-projection$
```

## Dependencies

```
$ pip install -e .
```

```
$ pip install tox
$ pip install pyaml-env
$ pip install pandas
$ pip install mongoengine
$ pip install minio
$ pip install scikit-learn
```

Installation your python pipeline packages in your virtual environment in development mode:

```
$ pip freeze > requirements.txt
```

# Docker

build image for local minikube environment:

```
docker build -t morphingprojections-job-projection:1.1.0 .

docker tag morphingprojections-job-projection:1.1.0 gsdpi/morphingprojections-job-projection:1.1.0

docker push gsdpi/morphingprojections-job-projection:1.1.0
```

build image for avib environment:

```
docker build --build-arg ARG_PYTHON_PROFILES_ACTIVE=avib -t morphingprojections-job-projection:1.1.0 .

docker tag morphingprojections-job-projection:1.1.0 gsdpi/morphingprojections-job-projection:1.1.0

docker push gsdpi/morphingprojections-job-projection:1.1.0
```

Execute job locally for a case_id 65cdc989fa8c8fdbcefac01e:

```
docker run --rm uniovi-avib-morphingprojections-job-projection:1.1.0 python src/morphingprojections_job_projection/service.py --case-id 65cdc989fa8c8fdbcefac01e --space primal,dual
```

## Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.