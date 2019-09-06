#!/usr/bin/env python
"""remove_fringe.py"""
import argparse
import glob
from fringe import remove_fringe


def return_model_template(fringe_model_folder):
    model = glob.glob(fringe_model_folder + '/fringe*model')[0]
    model_prefix = model.split('.')[0]
    model_suffix = '.'.join(model.split('.')[-2:])
    return model_prefix, model_suffix


def return_image_cid_qid(image):
    cid = image.split('_')[4]
    qid = image.split('_')[6]
    return cid, qid


def return_fringe_model(image, fringe_model_folder):
    model_prefix, model_suffix = return_model_template(fringe_model_folder)
    cid, qid = return_image_cid_qid(image)

    fringe_model = model_prefix
    fringe_model += '.%s_%s.' % (cid, qid)
    fringe_model += model_suffix

    return fringe_model


def main():
    """Subtracts a saved fringe model from the provided science image."""

    # Get arguments
    parser = argparse.ArgumentParser(description=__doc__)

    allArguments = parser.add_argument_group('arguments for '
                                             '--all-images-in-folder')
    allArguments.add_argument('--fringe-model-folder', type=str,
                              help='Folder that contains all fringe models.')

    notAllArguments = parser.add_argument_group('arguments for --single-image')
    notAllArguments.add_argument('--image-name', type=str,
                                 help='Filename of science image.')
    notAllArguments.add_argument('--fringe-model-name', type=str,
                                 help='Filename of fringe model.')

    allgroup = parser.add_mutually_exclusive_group()
    allgroup.add_argument('--all-images-in-folder', dest='allFlag',
                          action='store_true',
                          help='Clean all images in the current folder. '
                               'Selecting this parameter requires setting '
                               '--fringe-model-folder.')
    allgroup.add_argument('--single-image', dest='allFlag',
                          action='store_false',
                          help='Clean a single image. Selecting '
                               'this parameter requires setting '
                               '--image-name and --fringe-model-name. '
                               'DEFAULT.')
    parser.set_defaults(allFlag=False)

    plotgroup = parser.add_mutually_exclusive_group()
    plotgroup.add_argument('--debug', dest='debugFlag',
                           action='store_true',
                           help='Do save fringe image to disk.')
    plotgroup.add_argument('--debug-off', dest='debugFlag',
                           action='store_false',
                           help='Do NOT save fringe image to disk. DEFAULT.')
    parser.set_defaults(debugFlag=False)

    parallelgroup = parser.add_mutually_exclusive_group()
    parallelgroup.add_argument('--single', dest='parallelFlag',
                               action='store_false',
                               help='Run in single mode. DEFAULT.')
    parallelgroup.add_argument('--parallel', dest='parallelFlag',
                               action='store_true',
                               help='Run in parallel mode. This is '
                                    'recommended when selecting '
                                    '--all-images-in-folder.')
    parser.set_defaults(parallelFlag=False)

    args = parser.parse_args()

    if args.allFlag:
        if not args.fringe_model_folder:
            print('--fringe-model-folder must be set when '
                  '--all-images-in-folder is selected.')
            return
    else:
        if not args.image_name or not args.fringe_model_name:
            print('--image-name and --fringe-model-name must be set when '
                  '--single-image is selected.')
            return

    if args.allFlag:
        # Subtract the fringe model to all science images in the directory
        print('*** ---all-images-in-folder selected, cleaning all images '
              'in the current directory')
        images = glob.glob('ztf*sciimg.fits')

        if args.parallelFlag:
            from mpi4py import MPI
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            size = comm.Get_size()

            idx = rank
            while idx < len(images):
                image = images[idx]
                fringe_model = return_fringe_model(image,
                                                   args.fringe_model_folder)
                remove_fringe(image_name=image,
                              fringe_model_name=fringe_model,
                              debugFlag=args.debugFlag)
                idx += size
        else:
            for image in images:
                fringe_model = return_fringe_model(image,
                                                   args.fringe_model_folder)
                remove_fringe(image_name=image,
                              fringe_model_name=fringe_model,
                              debugFlag=args.debugFlag)
    else:
        # Subtract the fringe model from the --image-name science image
        print('*** ---single-image selected, cleaning a single image')
        remove_fringe(image_name=args.image_name,
                      fringe_model_name=args.fringe_model_name,
                      debugFlag=args.debugFlag)


if __name__ == '__main__':
    main()
