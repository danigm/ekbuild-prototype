from . import content
from . import image
from . import software


def main():
    print('Building Full Endless Key...')

    software.build()
    content.build()
    image.build()


if __name__ == '__main__':
    main()
