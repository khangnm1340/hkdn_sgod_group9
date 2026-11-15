OCR + face annotation
Frontend: React + Typescript
- Login, Dataset management, Annotation editor
Backend: Django + Django REST Framework : 
- Accounts: authentication and permission
- Datasets: Image uploads and management
- Annotations: OCR regions and face boxes
- Import / Export: Data Validation and Serialization
Database: PostgreSQL
- Users, datasets, annotations
Filestorage: Local
- Image and exports

# Things I learned
- A Foreign Key is a column that references the Primary Key of another table.
- Referential Integrity: A database principle that ensures relationships between tables remain valid by preventing records from referencing nonexistent records, keeping the data consistent and reliable.(CASCADE,PROTECT,SET_NULL,SET_DEFAULT)
- A model in Django is essentially a Python representation of a database table.

start with
```python
# accounts/models.py

from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass


# settings.py

AUTH_USER_MODEL = "accounts.User"
```


