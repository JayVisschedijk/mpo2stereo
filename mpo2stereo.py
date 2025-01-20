from __future__ import print_function
from optparse import OptionParser
from PIL import Image
from io import BytesIO
import errno, glob, os, sys


class MPOError(Exception):
    """Error class to distinguish improper file errors from possible IOErrors"""
    def __init__(self, value): self.value = value
    def __str__(self): return repr(self.value)


def split_mpo(filename):
    """Reads a given MPO file and finds the break between the two JPEG images."""

    with open(filename, 'rb') as f:
        data = f.read()

        # Look for the hex string 0xFFD9FFD8FFE1:
        #   0xFFD9 represents the end of the first JPEG image
        #   0xFFD8FFE1 marks the start of the appended JPEG image
        idx = data.find(b'\xFF\xD8\xFF\xE1', 1)

        if idx > 0:
            return Image.open(BytesIO(data[: idx])), Image.open(BytesIO(data[idx :]))
        else:
            raise MPOError(filename)

if __name__ == '__main__':
    parser = OptionParser('usage: %prog [options] mpofiles(s)')
    parser.add_option("-s", '--stereo', type="choice", choices=['parallel', 'crosseye'],
                  dest='stereo', help="Specify stereo type: 'parallel' or 'crosseye'.")
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error('invalid argument - requires at least one MPO file to read')
    elif len(args) == 1 and '*' in args[0]:
        args = glob.glob(args[0])

    for i, filename in enumerate(args):
        try:
            img_left, img_right = split_mpo(filename)

            if options.stereo:
                size = (2 * img_right.size[0], img_right.size[1])
                img_stereo = Image.new('RGB', size)

                if options.stereo == 'parallel':
                    img_stereo.paste(img_left, (0, 0))
                    img_stereo.paste(img_right, (img_right.size[0], 0))
                    filename = filename[:-4] +'_parallel.jpg'
                else:
                    img_stereo.paste(img_right, (0, 0))
                    img_stereo.paste(img_left, (img_right.size[0], 0))
                    filename = filename[:-4] +'_crosseye.jpg'

                print('Writing '+ filename +' (%d/%d)' % (i + 1, len(args)))
                img_stereo.save(filename)

            else:
                filename_l = filename[:-4] +'_left.jpg'
                print('Writing '+ filename_l+' (%d/%d)' % (i + 1, len(args)))
                img_left.save(filename_l)

                filename_r = filename[:-4] +'_right.jpg'
                print('Writing '+ filename_r +' (%d/%d)' % (i + 1, len(args)))
                img_right.save(filename_r)

        except MPOError:
            print(filename +' is not a valid MPO file')
        except IOError as e:
            print(filename +':')
            print('errno:', e.errno)
            print('err code:', errno.errorcode[e.errno])
            print('err message:', os.strerror(e.errno))
