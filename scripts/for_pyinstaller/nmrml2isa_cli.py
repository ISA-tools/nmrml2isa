from nmrml2isa import parsing, nmrml, isa
import pronto


if __name__ == '__main__':
    parsing.main()

    # this tmp list is so for automated checking
    # of code sees that we are using the imports
    # really they are just required for pyinstaller
    tmp = [nmrml, isa, pronto]
