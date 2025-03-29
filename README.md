MANUAL - CODERR (BACKEND)

Setting up the scrum board following the steps below:

1. Create a clone of this repository in an empty folder. The same applies to the frontend part (separate folder).
    - git clone <HTTPS-PATH>
2. Create an virtual environment in to the project folder with the following commands:
    - python3 -m venv <myenvname>
3. Activate the virual environment:
   - Windows: venv/Scripts/activate
   - Linux: source <base directory>/venv/bin/activate
3. Install all the dependencies from the requirements.txt file.
    - pip install -r /path/to/requirements.txt
4. If necessary, change the allowed ports in the settings.py file to the port your frontend uses. The default port is already set to 5500. 
   The port change is necessary to be able to process the requests.
    - ALLOWED_HOSTS / CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS
5. Set up the database.
    - python manage.py makemigrations
    - python manage.py migrate
6. Start the server 
    - python manage.py runserver
