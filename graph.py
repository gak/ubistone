#!/usr/bin/env python

import json
import xmlrpclib
import time
import multiprocessing

import keystone

'''
 - Link members together between projects. Same with forms (by name?).
'''

class GraphKeystoneAPI(object):

    def __init__(self):

        # settings
        self.settings = json.load(open('settings.json'))

        # ubigraph
        self.ubiurl = 'http://127.0.0.1:20738/RPC2'
        self.ubi().clear()

        # keystone
        self.ks = keystone.API(self.settings['host'])

        # index
        self.ubii = {}

        # locks!
        self.lock = multiprocessing.Lock()

    def ubi(self):
        return xmlrpclib.Server(self.ubiurl).ubigraph

    def new_vertex(self, name):
        v = self.ubi().new_vertex()
        self.ubii[name] = v
        return v

    def get_vertex(self, name):
        return self.ubii[name]

    def set_vertex_attribute(self, v, key, val):
        self.ubi().set_vertex_attribute(v, key, val)

    def go(self):
        print 'logging in as', self.settings['username']
        self.ks.login(self.settings['username'], self.settings['password'])
        print 'getting projects...'
        projects = self.ks.get_projects()

        print 'looping'

        self.lock.acquire()
        v = self.new_vertex('parent')
        self.set_vertex_attribute(v, 'label', self.settings['username'])
        self.set_vertex_attribute(v, 'color', '#ff0000')
        self.set_vertex_attribute(v, 'size', '2')
        self.set_vertex_attribute(v, 'shape', 'sphere')
        self.lock.release()
        
        for project in projects['data']:
            self.process_project(project)

    def process_project(self, project):
        self.lock.acquire()
        v = self.new_vertex('project' + str(project['id']))
        self.set_vertex_attribute(v, 'label', project['name'])
        self.set_vertex_attribute(v, 'color', '#ffffff')
        self.set_vertex_attribute(v, 'size', '2')
        self.set_vertex_attribute(v, 'shape', 'sphere')
        self.ubi().new_edge(self.get_vertex('parent'), v)
        self.lock.release()

        self.ks.get_blockheaders(project['id'],
                callback=self.handle_blockheaders)

    def handle_blockheaders(self, data, args):
        for blockheader in data['data']:
            self.process_blockheader(blockheader, args)

    def process_blockheader(self, blockheader, args):
        self.lock.acquire()
        v = self.new_vertex('blockheader' + str(blockheader['id']))
        self.set_vertex_attribute(v, 'color', '#00ff00')
        self.set_vertex_attribute(v, 'size', '1.5')
        self.set_vertex_attribute(v, 'shape', 'cube')
        p = self.get_vertex('project' + str(args['project_id']))
        self.ubi().new_edge(v, p)
        self.lock.release()

        self.ks.get_formtypeheaders(args['project_id'], blockheader['id'],
            callback=self.handle_formtypeheader)

    def handle_formtypeheader(self, data, args):
        for formtypeheader in data['data']:
            self.process_formtypeheader(formtypeheader, args)

    def process_formtypeheader(self, formtypeheader, args):
        self.lock.acquire()
        v = self.new_vertex('formtypeheader' + str(formtypeheader['id']))
        self.set_vertex_attribute(v, 'color', '#00ffff')
        self.set_vertex_attribute(v, 'size', '1.2')
        self.set_vertex_attribute(v, 'shape', 'dodecahedron')
        p = self.get_vertex('blockheader' + str(args['blockheader_id']))
        self.ubi().new_edge(v, p)
        self.lock.release()
        
        self.ks.get_filters(args['project_id'], args['blockheader_id'],
            formtypeheader['id'], callback=self.handle_filter)

    def handle_filter(self, data, args):
        for filter in data['data']:
            self.process_filter(filter, args)

    def process_filter(self, filter, args):
        self.lock.acquire()
        v = self.new_vertex('filter' + str(filter['id']))
        self.set_vertex_attribute(v, 'color', '#aaaaaa')
        self.set_vertex_attribute(v, 'size', '1')
        self.set_vertex_attribute(v, 'shape', 'octahedron')
        p = self.get_vertex('formtypeheader' + str(args['formtypeheader_id']))
        self.ubi().new_edge(v, p)
        self.lock.release()

        self.ks.get_filter_results(args['project_id'], filter['id'],
            callback=self.handle_filter_results)

    def handle_filter_results(self, data, args):
        print data
        sys.exit()
        for filter_result in data['data']:
            self.process_filter_result(filter_result, args)

    def process_filter_result(self, filter_result, args):
        self.lock.acquire()
        v = self.new_vertex('filter_result' + str(filter_result['id']))
        self.set_vertex_attribute(v, 'color', '#cccc00')
        self.set_vertex_attribute(v, 'size', '1')
        self.set_vertex_attribute(v, 'shape', 'cube')
        p = self.get_vertex('filter' + str(args['filter_id']))
        self.ubi().new_edge(v, p)
        self.lock.release()

def main():
    g = GraphKeystoneAPI()
    g.go()

if __name__ == '__main__':
    main()

