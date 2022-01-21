#imported from init.py in the package, the app is turned into a package to prevent circular import issues
from ucdgymbooker import app

#if this file is being run directly (e.g. not as an import), run the app
#TODO add config https://flask.palletsprojects.com/en/2.0.x/tutorial/factory/
if __name__ == "__main__":
    app.run(debug=True)