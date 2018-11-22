## Creating the project

```bash
cd flask_app
pip3 install virtualenv
virtualenv --python /usr/bin/python3.6 PAP
source PAP/bin/activate
pip install -r requirements.txt
deactivate
```

## Running the project 

```bash
source PAP/bin/activate
python app.py
```

## Stopping the server

```bash
deactivate
```