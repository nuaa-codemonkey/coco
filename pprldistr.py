#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""For generating empirical cumulative distribution function figures.

The outputs show empirical cumulative distribution functions (ECDFs) of
the running times of trials. These ECDFs show on the y-axis the fraction
of cases for which the running time (left subplots) or the df-value
(right subplots) was smaller than the value given on the x-axis. On the
left, ECDFs of the running times from trials are shown for different
target values. Light brown lines in the background show ECDFs for target
value 1e-8 of all algorithms benchmarked during BBOB-2009. On the right,
ECDFs of df-values from all trials are shown for different numbers of
function evaluations.

**Example**

.. plot::
   :width: 75%
   
   import urllib
   import tarfile
   import glob
   from pylab import *
   import bbob_pproc as bb
    
   # Collect and unarchive data (3.4MB)
   dataurl = 'http://coco.lri.fr/BBOB2009/pythondata/BIPOP-CMA-ES.tar.gz'
   filename, headers = urllib.urlretrieve(dataurl)
   archivefile = tarfile.open(filename)
   archivefile.extractall()
    
   # Empirical cumulative distribution function figure
   ds = bb.load(glob.glob('BBOB2009pythondata/BIPOP-CMA-ES/ppdata_f0*_20.pickle'))
   figure()
   bb.pprldistr.plot(ds)
   bb.pprldistr.beautify() # resize the window to view whole figure

"""
from __future__ import absolute_import

import os
import numpy as np
import pickle
import matplotlib.pyplot as plt
from pdb import set_trace
from bbob_pproc import bootstrap
from bbob_pproc.ppfig import consecutiveNumbers, plotUnifLogXMarkers, saveFigure, logxticks

# TODO: the target function values and the styles of the line only make sense
# together. Therefore we should either:
# 1. keep the targets as input argument and make rldStyles depend on them
# 2. remove the targets as input argument and put them here.
rldStyles = ({'color': 'k', 'ls': '--'},
             {'color': 'c'},
             {'color': 'm', 'ls': '--'},
             {'color': 'r', 'linewidth': 3.},
             {'color': 'k'},
             {'color': 'c'},
             {'color': 'm'},
             {'color': 'r'},
             {'color': 'k'},
             {'color': 'c'},
             {'color': 'm'},
             {'color': 'r'})
rldUnsuccStyles = ({'color': 'k', 'ls': '--'},
                   {'color': 'c'},
                   {'color': 'm', 'ls': '--'},
                   {'color': 'k'},
                   {'color': 'c', 'ls': '--'},
                   {'color': 'm'},
                   {'color': 'k', 'ls': '--'},
                   {'color': 'c'},
                   {'color': 'm', 'ls': '--'},
                   {'color': 'k'},
                   {'color': 'c', 'ls': '--'},
                   {'color': 'm'})  # should not be too short
refcolor = 'wheat'
nbperdecade = 1

# Used as a global to store the largest xmax and align the FV ECD figures.
fmax = None
evalfmax = None
figformat = ('eps', 'pdf') # Controls the output when using the main method

filename = 'pprldistr2009_1e-8.pickle'
filename = os.path.join(os.path.split(__file__)[0], filename)
isBestAlgorithmFound = True
try:
    f = open(filename,'r')
    dictbestalg = pickle.load(f)
except IOError, (errno, strerror):
    print "I/O error(%s): %s" % (errno, strerror)
    isBestAlgorithmFound = False
    print 'Could not find file: ', filename
else:
    f.close()


def beautifyECDF():
    """Generic formatting of ECDF figures."""
    plt.ylim(-0.01, 1.01)
    plt.yticks(np.array((0., 0.25, 0.5, 0.75, 1.0)),
               ('0.0', '', '0.5', '', '1.0'))
    plt.grid(True)
    xmin, xmax = plt.xlim()
    plt.xlim(xmin=xmin*0.90)
    c = plt.gca().get_children()
    for i in c: # TODO: we only want to extend ECDF lines...
        try:
            if i.get_drawstyle() == 'steps' and not i.get_linestyle() in ('', 'None'):
                xdata = i.get_xdata()
                ydata = i.get_ydata()
                if len(xdata) > 0:
                    #if xmin < min(xdata):
                    #    xdata = np.hstack((xmin, xdata))
                    #    ydata = np.hstack((ydata[0], ydata))
                    if xmax > max(xdata):
                        xdata = np.hstack((xdata, xmax))
                        ydata = np.hstack((ydata, ydata[-1]))
                    plt.setp(i, 'xdata', xdata, 'ydata', ydata)
            elif (i.get_drawstyle() == 'steps' and i.get_marker() != '' and
                  i.get_linestyle() in ('', 'None')):
                xdata = i.get_xdata()
                ydata = i.get_ydata()
                if len(xdata) > 0:
                    #if xmin < min(xdata):
                    #    minidx = np.ceil(np.log10(xmin) * nbperdecade)
                    #    maxidx = np.floor(np.log10(xdata[0]) * nbperdecade)
                    #    x = 10. ** (np.arange(minidx, maxidx + 1) / nbperdecade)
                    #    xdata = np.hstack((x, xdata))
                    #    ydata = np.hstack(([ydata[0]] * len(x), ydata))
                    if xmax > max(xdata):
                        minidx = np.ceil(np.log10(xdata[-1]) * nbperdecade)
                        maxidx = np.floor(np.log10(xmax) * nbperdecade)
                        x = 10. ** (np.arange(minidx, maxidx + 1) / nbperdecade)
                        xdata = np.hstack((xdata, x))
                        ydata = np.hstack((ydata, [ydata[-1]] * len(x)))
                    plt.setp(i, 'xdata', xdata, 'ydata', ydata)
        except (AttributeError, IndexError):
            pass

def beautifyRLD(evalfmax=None):
    """Format and save the figure of the run length distribution.
    
    After calling this function, changing the boundaries of the figure
    will not update the ticks and tick labels.
    
    """
    a = plt.gca()
    a.set_xscale('log')
    a.set_xlabel('log10 of FEvals / DIM')
    a.set_ylabel('proportion of trials')
    logxticks()
    if evalfmax:
        plt.xlim(xmax=evalfmax ** 1.05)
    plt.xlim(xmin=1.)
    beautifyECDF()

def beautifyFVD(isStoringXMax=False, ylabel=True):
    """Formats the figure of the run length distribution.

    This function is to be used with :py:func:`plotFVDistr`

    :param bool isStoringMaxF: if set to True, the first call
                               :py:func:`beautifyFVD` sets the global
                               :py:data:`fmax` and all subsequent call
                               will have the same maximum xlim
    :param bool ylabel: if True, y-axis will be labelled.

    """
    a = plt.gca()
    a.set_xscale('log')

    if isStoringXMax:
        global fmax
    else:
        fmax = None

    if not fmax:
        xmin, fmax = plt.xlim()
    plt.xlim(1., fmax)

    #axisHandle.invert_xaxis()
    a.set_xlabel('log10 of Df / Dftarget')
    if ylabel:
        a.set_ylabel('proportion of trials')
    logxticks()
    beautifyECDF()
    if not ylabel:
        a.set_yticklabels(())

def plotECDF(x, n=None, **plotArgs):
    """Plot an empirical cumulative distribution function.

    :param seq x: data
    :param int n: number of samples, if not provided len(x) is used
    :param plotArgs: optional keyword arguments provided to plot.

    :returns: handles of the plot elements.

    """
    if n is None:
        n = len(x)

    nx = len(x)
    if n == 0 or nx == 0:
        res = plt.plot([], [], **plotArgs)
    else:
        x = sorted(x) # do not sort in place
        x = np.hstack((x, x[-1]))
        y = np.hstack((np.arange(0., nx) / n, float(nx)/n))
        res = plotUnifLogXMarkers(x, y, nbperdecade=nbperdecade,
                                  drawstyle='steps', **plotArgs)
    return res

def plotERTDistr(dsList, target, **plotArgs):
    """Creates estimated run time distributions from a DataSetList.

    :keyword DataSet dsList: Input data sets
    :keyword dict target: target precision
    :keyword plotArgs: keyword arguments to pass to plot command

    :return: resulting plot.

    """
    x = []
    nn = 0
    samplesize = 1000 # samplesize is at least 1000
    percentiles = 0.5 # could be anything...

    for i in dsList:
        #funcs.add(i.funcId)
        for j in i.evals:
            if j[0] <= target[i.funcId]:
                runlengthsucc = j[1:][np.isfinite(j[1:])]
                runlengthunsucc = i.maxevals[np.isnan(j[1:])]
                tmp = bootstrap.drawSP(runlengthsucc, runlengthunsucc,
                                       percentiles=percentiles,
                                       samplesize=samplesize)
                x.extend(tmp[1])
                break
        nn += samplesize
    res = plotECDF(x, nn, **plotArgs)

    return res

def plotRLDistr(dsList, target, **plotArgs):
    """Creates run length distributions from a sequence dataSetList.

    Labels of the line (for the legend) will be set automatically with
    the following format: %+d: %d/%d % (log10()
    

    :param DataSetList dsList: Input data sets
    :param dict or float target: target precision
    :param plotArgs: additional arguments passed to the plot command

    :returns: handles of the resulting plot.

    """
    x = []
    nn = 0
    fsolved = set()
    funcs = set()
    for i in dsList:
        funcs.add(i.funcId)
        try:
            target = target[i.funcId]
        except TypeError:
            target = target
        tmp = i.detEvals((target, ))[0] / i.dim
        tmp = tmp[np.isnan(tmp) == False] # keep only success
        if len(tmp) > 0:
            fsolved.add(i.funcId)
        x.extend(tmp)
        nn += i.nbRuns()
    kwargs = plotArgs.copy()
    label = ''
    try:
        label += '%+d:' % (np.log10(target))
    except NameError:
        pass
    label += '%d/%d' % (len(fsolved), len(funcs))
    kwargs['label'] = kwargs.setdefault('label', label)
    res = plotECDF(x, nn, **kwargs)
    return res

def plotFVDistr(dsList, target, maxEvalsF, **plotArgs):
    """Creates ECDF of final function values plot from a DataSetList.
    
    :param dsList: data sets
    :param dict or float target: used for the lower limit of the plot
    :param float maxEvalsF: indicates which vertical data to display.
    :param plotArgs: additional arguments passed to plot

    :returns: handle

    """
    x = []
    nn = 0
    for i in dsList:
        for j in i.funvals:
            if j[0] >= maxEvalsF * i.dim:
                break
        try:
            tmp = j[1:].copy() / target[i.funcId]
        except TypeError:
            tmp = j[1:].copy() / target
        # Integrate the negative values of df / ftarget together
        # this is to prevent problem when passing on a log scale
        tmp[tmp<=0.] = min(np.append(tmp[tmp>0],[target])>0)
        x.extend(tmp)
        nn += i.nbRuns()
    res = plotECDF(x, nn, **plotArgs)
    return res

def comp(dsList0, dsList1, targets, isStoringXMax=False,
         outputdir='', info='default', verbose=True):
    """Generate figures of ECDF for 2 algorithms.

    Dashed lines will correspond to ALG0 and solid lines to ALG1.

    :param DataSetList dsList0: list of DataSet instances for ALG0
    :param DataSetList dsList1: list of DataSet instances for ALG1
    :param seq targets: target function values to be displayed
    :param bool isStoringXMax: if set to True, the first call
                               :py:func:`beautifyFVD` sets the globals
                               :py:data:`fmax` and :py:data:`maxEvals`
                               and all subsequent calls will use these
                               values as rightmost xlim in the generated
                               figures.
    :param string outputdir: output directory (must exist)
    :param string info: string suffix for output file names.
    :param bool verbose: control verbosity

    """
    #plt.rc("axes", labelsize=20, titlesize=24)
    #plt.rc("xtick", labelsize=20)
    #plt.rc("ytick", labelsize=20)
    #plt.rc("font", size=20)
    #plt.rc("legend", fontsize=20)

    dictdim0 = dsList0.dictByDim()
    dictdim1 = dsList1.dictByDim()
    for d in set(dictdim0.keys()) & set(dictdim1.keys()):
        maxEvalsFactor = max(max(i.mMaxEvals()/d for i in dictdim0[d]),
                             max(i.mMaxEvals()/d for i in dictdim1[d]))    
        if isStoringXMax:
            global evalfmax
        else:
            evalfmax = None
        if not evalfmax:
            evalfmax = maxEvalsFactor

        filename = os.path.join(outputdir,'pprldistr_%02dD_%s' % (d, info))
        fig = plt.figure()
        for j in range(len(targets)):
            tmp = plotRLDistr(dictdim0[d], targets[j], marker='+',
                              **rldStyles[j % len(rldStyles)])
            plt.setp(tmp[-1], label=None) # Remove automatic legend
            # Mods are added after to prevent them from appearing in the legend
            plt.setp(tmp, markersize=20.,
                     markeredgewidth=plt.getp(tmp[-1], 'linewidth'),
                     markeredgecolor=plt.getp(tmp[-1], 'color'),
                     markerfacecolor='none')
    
            tmp = plotRLDistr(dictdim1[d], targets[j], marker='o',
                              **rldStyles[j % len(rldStyles)])
            # modify the automatic legend: remover marker and change text
            plt.setp(tmp[-1], marker='', label=('%+d' % (np.log10(targets[j][1]))))
            # Mods are added after to prevent them from appearing in the legend
            plt.setp(tmp, markersize=15.,
                     markeredgewidth=plt.getp(tmp[-1], 'linewidth'),
                     markeredgecolor=plt.getp(tmp[-1], 'color'),
                     markerfacecolor='none')
    
        funcs = set(i.funcId for i in dictdim0[d]) | set(i.funcId for i in dictdim1[d])
        text = 'f%s' % (consecutiveNumbers(sorted(funcs)))
        plotBest2009(d, funcs)
        #plt.axvline(max(i.mMaxEvals()/i.dim for i in dictdim0[d]), ls='--', color='k')
        #plt.axvline(max(i.mMaxEvals()/i.dim for i in dictdim1[d]), color='k')
        plt.axvline(max(i.mMaxEvals()/i.dim for i in dictdim0[d]),
                    marker='+', markersize=20., color='k',
                    markeredgewidth=plt.getp(tmp[-1], 'linewidth',))
        plt.axvline(max(i.mMaxEvals()/i.dim for i in dictdim1[d]),
                    marker='o', markersize=15., color='k', markerfacecolor='None',
                    markeredgewidth=plt.getp(tmp[-1], 'linewidth'))
        plt.legend(loc='best')
        plt.text(0.5, 0.98, text, horizontalalignment="center",
                 verticalalignment="top", transform=plt.gca().transAxes)
                 #bbox=dict(ec='k', fill=False), 
        beautifyRLD(evalfmax)
        saveFigure(filename, figFormat=figformat, verbose=verbose)
        plt.close(fig)

def beautify():
    """Format the figure of the run length distribution.
    
    Used in conjunction with plot method.

    """
    plt.subplot(121)
    axisHandle = plt.gca()
    axisHandle.set_xscale('log')
    axisHandle.set_xlabel('log10 of FEvals / DIM')
    axisHandle.set_ylabel('proportion of trials')
    # Grid options
    logxticks()
    beautifyECDF()

    plt.subplot(122)
    axisHandle = plt.gca()
    axisHandle.set_xscale('log')
    xmin, fmax = plt.xlim()
    plt.xlim(1., fmax)
    axisHandle.set_xlabel('log10 of Df / Dftarget')
    beautifyECDF()
    logxticks()
    axisHandle.set_yticklabels(())
    plt.gcf().set_size_inches(16.35, 6.175)
#     try:
#         set_trace()
#         plt.setp(plt.gcf(), 'figwidth', 16.35)
#     except AttributeError: # version error?
#         set_trace()
#         plt.setp(plt.gcf(), 'figsize', (16.35, 6.))

def plot(dsList, targets=(10., 1e-1, 1e-4, 1e-8), **plotArgs):
    """Plot ECDF of evaluations and final function values."""

    assert len(dsList.dictByDim()) == 1, ('Cannot display different '
                                          'dimensionalities together')
    res = []

    plt.subplot(121)
    maxEvalsFactor = max(i.mMaxEvals()/i.dim for i in dsList)
    evalfmax = maxEvalsFactor
    for j in range(len(targets)):
        tmpplotArgs = dict(plotArgs, **rldStyles[j % len(rldStyles)])
        tmp = plotRLDistr(dsList, targets[j], **tmpplotArgs)
        res.extend(tmp)
    res.append(plt.axvline(x=maxEvalsFactor, color='k', **plotArgs))
    funcs = list(i.funcId for i in dsList)
    text = 'f%s' % (consecutiveNumbers(sorted(funcs)))
    res.append(plt.text(0.5, 0.98, text, horizontalalignment="center",
                        verticalalignment="top", transform=plt.gca().transAxes))

    plt.subplot(122)
    for j in range(len(targets)):
        tmpplotArgs = dict(plotArgs, **rldStyles[j % len(rldStyles)])
        tmp = plotFVDistr(dsList, targets[j], evalfmax, **tmpplotArgs)
        res.extend(tmp)
    tmp = np.floor(np.log10(evalfmax))
    # coloring right to left:
    maxEvalsF = np.power(10, np.arange(0, tmp))
    for j in range(len(maxEvalsF)):
        tmpplotArgs = dict(plotArgs, **rldUnsuccStyles[j % len(rldUnsuccStyles)])
        tmp = plotFVDistr(dsList, targets[-1], maxEvalsF[j], **tmpplotArgs)
        res.extend(tmp)
    res.append(plt.text(0.98, 0.02, text, horizontalalignment="right",
                        transform=plt.gca().transAxes))
    return res

def plotBest2009(dim, funcs):
    """Display BBOB 2009 data."""

    if isBestAlgorithmFound:
        for alg in dictbestalg:
            x = []
            nn = 0
            try:
                tmp = dictbestalg[alg]
                for f in funcs:
                    tmp[f][dim] # simply test that they exists
            except KeyError:
                continue

            for f in funcs:
                tmp2 = tmp[f][dim][0][1:]
                # [0], because the maximum #evals is also recorded
                # [1:] because the target function value is recorded
                x.append(tmp2[np.isnan(tmp2) == False])
                nn += len(tmp2)

            if x:
                x = np.hstack(x)
                plotECDF(x[np.isfinite(x)] / float(dim), nn,
                         color=refcolor, ls='-', zorder=-1)

def main(dsList, targets, isStoringXMax=False, outputdir='',
         info='default', verbose=True):
    """Generate figures of empirical cumulative distribution functions.
    
    This method has a feature which allows to keep the same boundaries
    for the x-axis. This makes sense when dealing with different
    functions or subsets of functions for one given dimension.

    :param DataSetList dsList: list of DataSet instances to process.
    :param seq targets: target precisions to be displayed
    :param bool isStoringXMax: if set to True, the first call
                               :py:func:`beautifyFVD` sets the
                               globals :py:data:`fmax` and
                               :py:data:`maxEvals` and all subsequent
                               calls will use these values as rightmost
                               xlim in the generated figures.
    :param string outputdir: output directory (must exist)
    :param string info: string suffix for output file names.
    :param bool verbose: control verbosity
    
    """
    #plt.rc("axes", labelsize=20, titlesize=24)
    #plt.rc("xtick", labelsize=20)
    #plt.rc("ytick", labelsize=20)
    #plt.rc("font", size=20)
    #plt.rc("legend", fontsize=20)

    for d, dictdim in dsList.dictByDim().iteritems():
        maxEvalsFactor = max(i.mMaxEvals() / d for i in dictdim)
        if isStoringXMax:
            global evalfmax
        else:
            evalfmax = None
        if not evalfmax:
            evalfmax = maxEvalsFactor
    
        filename = os.path.join(outputdir,'pprldistr_%02dD_%s' % (d, info))
        fig = plt.figure()
        for j in range(len(targets)):
            tmp = plotRLDistr(dictdim, targets[j],
                              **rldStyles[j % len(rldStyles)])
    
        funcs = list(i.funcId for i in dictdim)
        text = 'f%s' % (consecutiveNumbers(sorted(funcs)))
        plotBest2009(d, funcs)
        plt.axvline(x=maxEvalsFactor, color='k')
        plt.legend(loc='best')
        plt.text(0.5, 0.98, text, horizontalalignment="center",
                 verticalalignment="top", transform=plt.gca().transAxes)
                 #bbox=dict(ec='k', fill=False), 
        beautifyRLD(evalfmax)
        saveFigure(filename, figFormat=figformat, verbose=verbose)
        plt.close(fig)
    
        filename = os.path.join(outputdir,'ppfvdistr_%02dD_%s' % (d, info))
        fig = plt.figure()
        for j in range(len(targets)):
            tmp = plotFVDistr(dictdim, targets[j], evalfmax,
                              **rldStyles[j % len(rldStyles)])
        tmp = np.floor(np.log10(evalfmax))
        # coloring left to right:
        #maxEvalsF = np.power(10, np.arange(tmp, 0, -1) - 1)
        # coloring right to left:
        maxEvalsF = np.power(10, np.arange(0, tmp))
        for j in range(len(maxEvalsF)):
            tmp = plotFVDistr(dictdim, targets[-1], maxEvalsF[j],
                              **rldUnsuccStyles[j % len(rldUnsuccStyles)])    
        plt.text(0.98, 0.02, text, horizontalalignment="right",
                 transform=plt.gca().transAxes)
                 #bbox=dict(ec='k', fill=False), 
        beautifyFVD(isStoringXMax=isStoringXMax, ylabel=False)
        saveFigure(filename, figFormat=figformat, verbose=verbose)
        plt.close(fig)
        #plt.rcdefaults()
