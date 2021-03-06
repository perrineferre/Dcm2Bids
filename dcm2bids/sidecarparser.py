# -*- coding: utf-8 -*-


import itertools
import os
from collections import defaultdict, OrderedDict
from future.utils import iteritems
from .structure import Acquisition
from .utils import load_json, splitext_


class Sidecarparser(object):

    def __init__(self, sidecars, descriptions):
        self.sidecars = sidecars
        self.descriptions = descriptions
        self.graph = self._generateGraph()
        self.acquisitions = self._generateAcquisitions()
        self.findRuns()


    def _generateGraph(self):
        graph = OrderedDict((_, []) for _ in self.sidecars)
        for sidecar, index in itertools.product(
                self.sidecars, range(len(self.descriptions))):
            self._sidecar = load_json(sidecar)
            if self._respect(self.descriptions[index]["criteria"]):
                graph[sidecar].append(index)
        return graph


    def _generateAcquisitions(self):
        rsl = []
        print("")
        for sidecar, match_descs in iteritems(self.graph):
            base = splitext_(sidecar)[0]
            basename = os.path.basename(sidecar)
            if len(match_descs) == 1:
                print("'{}' satisfies one description".format(basename))
                acq = self._acquisition(
                        base, self.descriptions[match_descs[0]])
                rsl.append(acq)
            elif len(match_descs) == 0:
                print("'{}' satisfies no description".format(basename))
            else:
                print("'{}' satisfies several descriptions".format(basename))
        return rsl


    def findRuns(self):
        def list_duplicates(seq):
            """
            http://stackoverflow.com/a/5419576
            """
            tally = defaultdict(list)
            for i, item in enumerate(seq):
                tally[item].append(i)
            return ((key,locs) for key,locs in tally.items() if len(locs)>1)

        suffixes = [_.suffix for _ in self.acquisitions]
        for suffix, dup in sorted(list_duplicates(suffixes)):
            print("'{}': has several runs".format(suffix))
            for run, acq_index in enumerate(dup):
                runStr = "run-{:02d}".format(run+1)
                acq = self.acquisitions[acq_index]
                if acq.customLabels is None:
                    acq.customLabels = runStr
                else:
                    acq.customLabels += "_" + runStr
        print("")


    def _acquisition(self, base, desc):
        acq = Acquisition(base, desc["dataType"], desc["suffix"])
        if "customLabels" in desc:
            acq.customLabels = desc["customLabels"]
        else:
            acq.customLabels = None
        return acq


    def _respect(self, criteria):
        isEqual = "equal" in criteria
        isIn = "in" in criteria

        # Check if there is some criteria
        if not any([isEqual, isIn]):
            return False

        if isEqual:
            rsl_equal = self._isEqual(criteria["equal"])
        else:
            rsl_equal = True

        if isIn:
            rsl_in = self._isIn(criteria["in"])
        else:
            rsl_in = True

        return all([rsl_equal, rsl_in])


    def _isEqual(self, criteria):
        rsl = []
        for tag, query in iteritems(criteria):
            rsl.append(query == self.get_value(tag))
        return all(rsl)


    def _isIn(self, criteria):
        rsl = []
        for tag, query in iteritems(criteria):
            if isinstance(query, list):
                for q in query:
                    rsl.append(q in self.get_value(tag))
            else:
                rsl.append(query in self.get_value(tag))
        return all(rsl)


    def get_value(self, tag):
        if tag in self._sidecar:
            return self._sidecar[tag]
        else:
            return ""

