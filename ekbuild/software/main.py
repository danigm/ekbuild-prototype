from . import app
from . import launcher
from . import plugins


def main():
    # TODO:
    #  * Cache the software and download only if there's a new release
    #  * Download software from github release or pypi
    print('Building EK Software')
    app.download()
    launcher.download()
    plugins.download()
