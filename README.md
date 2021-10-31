# scrud-django
A Django application for SCRUD REST services. Semantic REST API generation.

## Installation

```bash
pip install scrud-django
```

## Configuration

### Required

Add `scrud_django`, `scoped_rbac`, and `django_jsonfield_backport` to  `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
  ...
  'django_jsonfield_backport',
  'scoped_rbac',
  'scrud_django',
  ...
]
```

### Optional

Scrud Django can return [RFC 7807](https://tools.ietf.org/html/rfc7807) responses. To
configure this add the Scrud Django exception handler for Django REST Framework in your
`settings.py`.

```python
REST_FRAMEWORK = {
  "EXCEPTION_HANDLER": "scrud_django.exceptions.scrud_exception_handler",
  ...
}
```

## Development Get Started

### Get prepared to run tests and the demo application

```bash
cd docker
conda env create -f environment-dev.yml
conda activate scrud-django
cd ..
make develop
make migrate
```
### Confirm setup

```bash
make run_tests
```

### Start the demo application

```bash
cd demo
python manage.py runserver
```

