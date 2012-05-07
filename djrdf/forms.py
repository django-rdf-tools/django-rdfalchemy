# -*- coding:utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from djrdf.models import djRdf
from formalchemy.ext.rdf import FieldSet, Grid


class djRdfForm():
    model = djRdf

    def form(self, obj):
        fs = FieldSet(self.model)
        fs = self._configure(fs, obj)
        fs = fs.bind(obj)
        return fs

    def grid(self, obj):
        fs = Grid(self.model, [obj])
        fs = obj._configure(fs)
        return fs
