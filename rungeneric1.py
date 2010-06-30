#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Module for post-processing the data of one algorithm.
   Calls the function main with arguments from the command line. Executes the
   postprocessing on the given files and folders arguments, using the .info
   files found recursively.

Synopsis:
    python path_to_folder/bbob_pproc/rungeneric1.py [OPTIONS] FILE_NAME FOLDER_NAME...
Help:
    python path_to_folder/bbob_pproc/rungeneric1.py -h

"""

from __future__ import absolute_import

import os
import sys
import warnings
import getopt
from pdb import set_trace
import matplotlib
matplotlib.use('Agg') # To avoid window popup and use without X forwarding

# Add the path to bbob_pproc
if __name__ == "__main__":
    # os.path.split is system independent
    (filepath, filename) = os.path.split(sys.argv[0])
    sys.path.append(os.path.join(filepath, os.path.pardir))

from bbob_pproc import pptex, pptable, pprldistr, ppfigdim, pplogloss, findfiles
from bbob_pproc.pproc import DataSetList

import matplotlib.pyplot as plt

# Used by getopt:
shortoptlist = "hvpfo:"
longoptlist = ["help", "output-dir=", "noisy", "noise-free", "tab-only",
               "fig-only", "rld-only", "los-only", "crafting-effort=",
               "pickle", "verbose", "final"]

#CLASS DEFINITIONS

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg


#FUNCTION DEFINITIONS

def usage():
    print main.__doc__

def main(argv=None):
    """Generates from BBOB experiment data some outputs for a TeX document.

    Provided with some index entries (found in files with the 'info' extension)
    this routine outputs figure and TeX files in the folder 'ppdata' needed for
    the compilation of latex document template1.tex. These output files will
    contain performance tables, performance scaling figures and
    empirical cumulative distribution figures. On subsequent executions, new
    files will be added to the output directory, overwriting existing older
    files in the process.

    Keyword arguments:
    argv -- list of strings containing options and arguments. If not given,
    sys.argv is accessed.

    argv should list either names of info files or folders containing info
    files. argv can also contain post-processed pickle files generated by this
    routine. Furthermore, argv can begin with, in any order, facultative option
    flags listed below.

        -h, --help

            display this message

        -v, --verbose

            verbose mode, prints out operations. When not in verbose mode, no
            output is to be expected, except for errors.

        -p, --pickle

            generates pickle post processed data files.

        -o, --output-dir OUTPUTDIR

            change the default output directory ('ppdata') to OUTPUTDIR

        --crafting-effort=VALUE

            sets the crafting effort to VALUE (float). Otherwise the user will
            be prompted. This flag is useful when running this script in batch.

        -f, --final

            lengthens the bootstrapping process used as dispersion measure in
            the tables generation. This might at least double the time of the
            whole post-processing.

        --noise-free, --noisy

            restrain the post-processing to part of the data set only.

        --tab-only, --fig-only, --rld-only, --los-only

            these options can be used to output respectively the tex tables,
            convergence and ERTs graphs figures, run length distribution
            figures, ERT loss ratio figures only. A combination of any two of
            these options results in no output.

    Exceptions raised:
    Usage -- Gives back a usage message.

    Examples:

    * Calling the rungeneric1.py interface from the command line:

        $ python bbob_pproc/rungeneric1.py -v experiment1

    will post-process the folder experiment1 and all its containing data,
    base on the found .info files in the folder. The result will appear
    in folder ppdata. The -v option adds verbosity.

        $ python bbob_pproc/rungeneric1.py -o otherppdata experiment2/*.info

    This will execute the post-processing on the info files found in
    experiment2. The result will be located in the alternative location
    otherppdata.

    * Loading this package and calling the main from the command line
      (requires that the path to this package is in python search path):

        $ python -m bbob_pproc.rungeneric1 -h

    This will print out this help message.

    * From the python interactive shell (requires that the path to this
      package is in python search path):

        >>> from bbob_pproc import rungeneric1
        >>> rungeneric1.main('-o outputfolder folder1'.split())

    This will execute the post-processing on the index files found in folder1.
    The -o option changes the output folder from the default ppdata to
    outputfolder.

    """

    if argv is None:
        argv = sys.argv[1:]
        # The zero-th input argument which is the name of the calling script is
        # disregarded.

    try:

        try:
            opts, args = getopt.getopt(argv, shortoptlist, longoptlist)
        except getopt.error, msg:
             raise Usage(msg)

        if not (args):
            usage()
            sys.exit()

        inputCrE = None
        isfigure = True
        istab = True
        isrldistr = True
        islogloss = True
        isPostProcessed = False
        isPickled = False
        isDraft = True
        verbose = False
        outputdir = 'ppdata'
        isNoisy = False
        isNoiseFree = False

        #Process options
        for o, a in opts:
            if o in ("-v","--verbose"):
                verbose = True
            elif o in ("-h", "--help"):
                usage()
                sys.exit()
            elif o in ("-p", "--pickle"):
                isPickled = True
            elif o in ("-o", "--output-dir"):
                outputdir = a
            elif o in ("-f", "--final"):
                isDraft = False
            elif o == "--noisy":
                isNoisy = True
            elif o == "--noise-free":
                isNoiseFree = True
            #The next 4 are for testing purpose
            elif o == "--tab-only":
                isfigure = False
                isrldistr = False
                islogloss = False
            elif o == "--fig-only":
                istab = False
                isrldistr = False
                islogloss = False
            elif o == "--rld-only":
                istab = False
                isfigure = False
                islogloss = False
            elif o == "--los-only":
                istab = False
                isfigure = False
                isrldistr = False
            elif o == "--crafting-effort":
                try:
                    inputCrE = float(a)
                except ValueError:
                    raise Usage('Expect a valid float for flag crafting-effort.')
            else:
                assert False, "unhandled option"

        #TODO what if multiple output dir and crafting effort?

        if False:
            from bbob_pproc import bbob2010 as inset # input settings
            # is here because variables setting could be modified by flags
        else:
            from bbob_pproc import genericsettings as inset # input settings

        if (not verbose):
            warnings.simplefilter('ignore')

        print ("BBOB Post-processing: will generate post-processing " +
               "data in folder %s" % outputdir)
        print "  this might take several minutes."

        filelist = list()
        for i in args:
            if os.path.isdir(i):
                filelist.extend(findfiles.main(i, verbose))
            elif os.path.isfile(i):
                filelist.append(i)
            else:
                txt = 'Input file or folder %s could not be found.' % i
                raise Usage(txt)

        dsList = DataSetList(filelist, verbose)

        if not dsList:
            raise Usage("Nothing to do: post-processing stopped.")

        if isNoisy and not isNoiseFree:
            dsList = dsList.dictByNoise().get('nzall', DataSetList())
        if isNoiseFree and not isNoisy:
            dsList = dsList.dictByNoise().get('noiselessall', DataSetList())

        if (verbose):
            for i in dsList:
                if (dict((j, i.itrials.count(j)) for j in set(i.itrials)) !=
                    inset.instancesOfInterest):
                    warnings.warn('The data of %s do not list ' %(i) +
                                  'the correct instances ' +
                                  'of function F%d.' %(i.funcId))

        dictAlg = dsList.dictByAlg()
        if len(dictAlg) > 1:
            warnings.warn('Data with multiple algId %s ' % (dictAlg) +
                          'will be processed together.')
            #TODO: in this case, all is well as long as for a given problem
            #(given dimension and function) there is a single instance of
            #DataSet associated. If there are more than one, the first one only
            #will be considered... which is probably not what one would expect.
            #TODO: put some errors where this case would be a problem.
            # raise Usage?

        if isfigure or istab or isrldistr or islogloss:
            if not os.path.exists(outputdir):
                os.makedirs(outputdir)
                if verbose:
                    print 'Folder %s was created.' % (outputdir)

        if isPickled:
            dsList.pickle(verbose=verbose)

        if isfigure:
            #ERT/dim vs dim.
            plt.rc("axes", **inset.rcaxeslarger)
            plt.rc("xtick", **inset.rcticklarger)
            plt.rc("ytick", **inset.rcticklarger)
            plt.rc("font", **inset.rcfontlarger)
            plt.rc("legend", **inset.rclegendlarger)
            ppfigdim.ertoverdimvsdim(dsList, inset.figValsOfInterest,
                                     outputdir, verbose)
            print "Scaling figures done."

        plt.rc("axes", **inset.rcaxes)
        plt.rc("xtick", **inset.rctick)
        plt.rc("ytick", **inset.rctick)
        plt.rc("font", **inset.rcfont)
        plt.rc("legend", **inset.rclegend)

        if istab:
            dictNoise = dsList.dictByNoise()
            for noise, sliceNoise in dictNoise.iteritems():
                pptable.main(sliceNoise, inset.tabDimsOfInterest, outputdir,
                             noise, verbose)
            print "TeX tables",
            if isDraft:
                print ("(draft) done. To get final version tables, please "
                       "use the -f option")
            else:
                print "done."

        if isrldistr:
            dictNoise = dsList.dictByNoise()
            if len(dictNoise) > 1:
                warnings.warn('Data for functions from both the noisy and '
                              'non-noisy testbeds have been found. Their '
                              'results will be mixed in the "all functions" '
                              'ECDF figures.')
            dictDim = dsList.dictByDim()
            for dim in inset.rldDimsOfInterest:
                try:
                    sliceDim = dictDim[dim]
                except KeyError:
                    continue

                pprldistr.main2(sliceDim, inset.rldValsOfInterest, True,
                               outputdir, 'dim%02dall' % dim, verbose)
                dictNoise = sliceDim.dictByNoise()
                for noise, sliceNoise in dictNoise.iteritems():
                    pprldistr.main2(sliceNoise, inset.rldValsOfInterest, True,
                                   outputdir, 'dim%02d%s' % (dim, noise),
                                   verbose)
                dictFG = sliceDim.dictByFuncGroup()
                for fGroup, sliceFuncGroup in dictFG.items():
                    pprldistr.main2(sliceFuncGroup, inset.rldValsOfInterest, True,
                                   outputdir, 'dim%02d%s' % (dim, fGroup),
                                   verbose)

                pprldistr.fmax = None #Resetting the max final value
                pprldistr.evalfmax = None #Resetting the max #fevalsfactor

            print "ECDF graphs done."

        if islogloss:
            for ng, sliceNoise in dsList.dictByNoise().iteritems():
                if ng == 'noiselessall':
                    testbed = 'noiseless'
                elif ng == 'nzall':
                    testbed = 'noisy'
                txt = ("Please input crafting effort value "
                       + "for %s testbed:\n  CrE = " % testbed)
                CrE = inputCrE
                while CrE is None:
                    try:
                        CrE = float(input(txt))
                    except (SyntaxError, NameError, ValueError):
                        print "Float value required."
                dictDim = sliceNoise.dictByDim()
                for d in inset.rldDimsOfInterest:
                    try:
                        sliceDim = dictDim[d]
                    except KeyError:
                        continue
                    info = 'dim%02d%s' % (d, ng)
                    pplogloss.main(sliceDim, CrE, True, outputdir, info,
                                   verbose=verbose)
                    pplogloss.generateTable(sliceDim, CrE, outputdir, info,
                                            verbose=verbose)
                    for fGroup, sliceFuncGroup in sliceDim.dictByFuncGroup().iteritems():
                        info = 'dim%02d%s' % (d, fGroup)
                        pplogloss.main(sliceFuncGroup, CrE, True, outputdir, info,
                                       verbose=verbose)
                    pplogloss.evalfmax = None #Resetting the max #fevalsfactor

            print "ERT loss ratio figures and tables done."

        if isfigure or istab or isrldistr or islogloss:
            print "Output data written to folder %s." % outputdir

        plt.rcdefaults()

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use -h or --help"
        return 2


if __name__ == "__main__":
   sys.exit(main())
