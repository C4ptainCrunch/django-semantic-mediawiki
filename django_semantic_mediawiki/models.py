# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
import requests
import collections
import json
from django.conf import settings

# TODO :
# support .exclude filters
# support slicing
# cache http requests
# support > < <= >= filters


class WikiManager(models.Manager):

    def get_query_set(self):
        return WikiQuerySet(self.model)

    def __getattr__(self, name):
        return getattr(self.get_query_set(), name)


class WikiQuerySet(object):

    def __init__(self, model=None, query={}, using=None):
        self.model = model
        self.query = query
        self.executed = False

        self._cache = []
        self._cache_full = False

        if using is None:
            try:
                using = settings.DATABASES['semantic']['NAME']
            except KeyError:
                raise Exception("No API selected. You should either add an api url in settings.DATABASES['semantic']['NAME']"
                    + " or specify an url with the 'using' parameter "
                    + "(eg: Model.objects.all(using='http://wiki.urlab.be/api.php?action=ask&query=')) ")

        self.using = using

    def all(self):
        return WikiQuerySet(model=self.model, query=self.query, using=self.using)

    _clone = all

    def _request_crafter(self, i):
        if "order" in self.query:
            sort, order = [], []
            for conventional, col in self.query['order']:
                sign = "ASC" if conventional else "DESC"
                order.append(sign)
                sort.append(col)
            sort_str = "|sort={sort}|order={order}".format(sort=','.join(sort), order=','.join(order))
        else:
            sort_str = ""

        columns = filter(lambda x: not x is None, map(lambda x: x.db_column, self.model._meta.fields))

        columns_str = ''.join(map(lambda x: "|?" + x, columns))

        return "{domain}[[Category:{model}]]{sort}{columns}|offset={offset}&format=json".format(
            domain=self.using,
            sort=sort_str,
            model=self.model._meta.object_name,
            columns=columns_str,
            offset=i
        )

    def _http(self, url):
        print "R = {} ".format(url)
        # Insert cache here
        return requests.get(url)

    def _deserialize(self, text):
        return json.loads(text, object_pairs_hook=collections.OrderedDict, encoding='unicode_escape')

    @property
    def ordered(self):
        return "order" in self.query

    def reverse(self):
        # TODO : Check if query if done
        if not self.ordered:
            raise Exception('Cannot reverse non-ordered query.')
        clone = self.all()
        clone.query['order'] = map(lambda (order, key): (not order, key), self.query['order'])

        return clone

    def order_by(self, *fields):
        if self.executed:
            raise Exception('Cannot order a query once it has been executed.')
        clone = self.all()
        if not self.ordered:
            clone.query['order'] = []
        fields = map(lambda x: (x[0] != "-", x[1:] if x[0] == "-" else x),
            fields)
        clone.query['order'] += fields

        return clone

    def __len__(self):
        return len(list(self.iterator()))

    count = __len__

    def get(self, *args, **kwargs):
        clone = self.filter(*args, **kwargs)
        # Should be len(clone[:2])
        num = len(clone)
        if num == 1:
            return clone._create_model(clone.result[0])
        if not num:
            raise self.model.DoesNotExist(
                "%s matching query does not exist." %
                self.model._meta.object_name)
        raise self.model.MultipleObjectsReturned(
            "get() returned more than one %s -- it returned %s!" %
            (self.model._meta.object_name, num))

    def iterator(self):
        i = 0
        if not self.executed:
            self.executed = True
            self.end = False
        else:
            for elem in self._cache:
                i += 1
                yield elem

        if not self._cache_full:
            while not self.end:
                url = self._request_crafter(i=i)
                j = self._deserialize(self._http(url).text)
                response = j['query']['results']

                self.end = not 'query-continue' in j

                for key, item in response.iteritems():
                    i += 1
                    new_item = {}
                    new_item['key'] = ':'.join(key.split(':')[1:])
                    new_item['url'] = item['fullurl']
                    for colum, value in item['printouts'].iteritems():
                        new_item[colum] = value

                    obj = self._create_model(new_item)
                    self._cache.append(obj)

                    yield obj
        self._cache_full = True

    __iter__ = iterator

    def __getitem__(self, k):
        # TODO : FIX THIS !!! Should not get everything !
        return list(self).__getitem__(k)

    def _create_model(self, line):
        fields = filter(lambda x: not x.db_column is None, self.model._meta.fields)
        cols = {}
        for field in fields:
            cols[field.name] = line[field.db_column.capitalize()]
        return self.model(name=line['key'], url=line['url'], **cols)

    def filter(self, *args, **kwargs):
        if self.executed:
            raise Exception('Cannot filter a query once it has been executed.')

        clone = self.all()
        for key in kwargs:
            val = kwargs[key]
            if not key == 'Category':
                key += ":"
            clone.query += "[[{}:{}]]".format(key, val)
        return clone


class WikiCharField(models.CharField):

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 500
        super(WikiCharField, self).__init__(*args, **kwargs)


class WikiModel(models.Model):
    objects = WikiManager()

    class Meta:
        abstract = True
        managed = False
