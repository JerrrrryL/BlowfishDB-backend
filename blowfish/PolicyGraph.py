import numpy as np
import json
import itertools

#TODO Do not suppport granularity level now

class PolicyGraph:
    """domain of the database and corresponding graph"""

    def __init__(self):
        """the following attributes will be specified in domain.json file"""
        self.domain = {}  # column name: domain i.e 'age':{1,2,..,100} shall be a set for categorical val
        self.attr_type = {}  # attribute name: categorical/numerical
        self.attr_names = []  # column names
        self.numAttributes = 0
        self.threshold = {}  # default to 1
        self.sensitiveSet = {}

        """the following attributes will be specified wrt each query"""
        self.numEdges = {}  # # of edges connecting two non-null vertices
        self.numNullEdges = {}  # # of edges involving null vertex
        self.edges = []  # edges in the policy graph connecting two non-null vertices
        self.vertices = []  # vertices in the policy graph where each vertex matches the order of self.attr_names

        self.unbounded = True  # if we include <bot> or not
        self.PG = []  # PG matrix
        self.crossVariable = 0  # 0 represents or and 1 represents and
        self.policyTemplate = {}  # template wrt each attribute


    # category data: if the pair has both values in the sensitivity set, return True
    # Otherwise, return False
    #v1, v2 are values within one attribute
    def category_policy(self, v1, v2, attr_name):
        sensitivity_set = self.sensitiveSet[attr_name]
        if v1 in sensitivity_set and v2 in sensitivity_set:
            return True
        else:
            return False

    def set_domain(self, data):
        self.numAttributes = len(data.keys())
        for attr_name in data.keys():
            attr_type = data[attr_name]['type']
            # TODO: right now we are treating the domain as sets from a json file
            #attr_domain = set(data[attr_name]['domain'])
            attr_policy_dict = data[attr_name]['policy']
            #self.domain[attr_name] = attr_domain
            self.unbounded = bool(attr_policy_dict["bot"])
            template = attr_policy_dict["template"]
            self.policyTemplate[attr_name] = template
            self.attr_type[attr_name] = attr_type
            self.numEdges[attr_name] = 0
            self.numNullEdges[attr_name] = 0
            if attr_type == "Numerical":
                threshold = attr_policy_dict["graph"] #TODO rename
                self.threshold[attr_name] = threshold
            else:
                threshold = set(attr_policy_dict["graph"])
                self.sensitiveSet[attr_name] = threshold

    # INPUT: attr_bags, {"age": [(1,2),(3,4)]} or {"age":[(1), (2), (3), (4)]}
    def set_vertices(self, attr_bags):
        T = []
        for ele in sorted(attr_bags.keys()): #sorted to ensure consitent order in PG and x
            self.attr_names.append(ele)
            T.append(attr_bags[ele])
        self.vertices = list(itertools.product(*T))
        if self.unbounded:
            self.vertices.append([-1])
        self.num_vertices = len(self.vertices)

    # take in 2 vertices and decide if there shall be an edge between them
    def edge_exist(self, vertex1, vertex2):
        edge_AND = True
        for i in range(len(self.attr_names)):
            attr_name = self.attr_names[i]
            attr_type = self.attr_type[attr_name]
            val1, val2 = vertex1[i], vertex2[i] #val1, val2 are values of one attribute
            single_edge = False
            if attr_type == 'Numerical':
                single_edge = abs(val1-val2) <= self.threshold[attr_name]
            else:
                single_edge = self.category_policy(val1, val2, attr_name)
            if self.crossVariable == 0 and single_edge:
                return True
            edge_AND = edge_AND and single_edge
        return edge_AND


    # TODO: do not consider unbounded now
    def construct_PG(self):
        num_vertices = len(self.vertices)
        for i in range(num_vertices):
            for j in range(i+1, num_vertices): #TODO: is this correct?
                if self.edge_exist(self.vertices[i], self.vertices[j]):
                    self.edges.append((i, j))
        self.PG = np.zeros(shape=(num_vertices,len(self.edges)))
        for i, edge in enumerate(self.edges):
            self.PG[edge[0]][i] = 1
            self.PG[edge[1]][i] = -1

# config = open('pre_scan.json')
# data = json.load(config)
# config.close()
# bags = {"age": [(1),(2),(3),(4),(5),(6),(7)]}
# P = PolicyGraph()
# P.set_domain(data)
# P.set_vertices(bags)
# P.construct_PG()
