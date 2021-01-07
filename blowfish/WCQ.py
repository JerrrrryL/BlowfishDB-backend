from collections import defaultdict
import numpy as np

class WCQ:
    #salary 1~50, age 18~100
    def __init__(self, cols, conds, table):
        self.columns = cols #[salary, age]
        self.domain_per_column = defaultdict(set)
        self.predicates = conds #["salary >= 0 AND salary <= 20 AND age <= 20"]
        #the columns in predicates should be ordered 
        self.table_name = table

        #For intermediate result
        self.PG = None
        self.W = None
        self.x= None

        #For results
        self.true_answer = None
        self.noisy_answer = None
        self.answer_diff = None

    
    #SELECT id, [col1], [col2] FROM table1
    def generate_base_query(self):
        query = "SELECT id"
        for col in self.columns:
            query += ", {}".format(col)
        query += " FROM {}".format(self.table_name)
        return query
        
    #generate x and W
    def run_query(self, db):
        base_query = self.generate_base_query()
        results_by_query = []
        print("Running queries...")
        #execute the query to retrieve [(id, val1, val2, ...)]
        #collect present values for each column
        for pred in self.predicates:
            res = db.run(base_query+' WHERE '+pred)
            for i in range(len(self.columns)):
                self.domain_per_column[self.columns[i]].update([record[i+1] for record in res])
            results_by_query.append(res)
        print("Collecting domain for each column...")
        #calculate size of x
        total_size = 1
        for col in self.columns:
            total_size *= len(self.domain_per_column[col])
        assert total_size > 0
        #generate a mapping for val of each column to its sorted index in the column domain
        #e.g. column_domain:{3,1,2}, value 1 maps to index 0
        value_to_index_per_column = defaultdict(dict)
        for col in self.columns:
            vals = list(self.domain_per_column[col])
            indices = np.argsort(vals)
            for i in range(len(vals)):
                value_to_index_per_column[col][vals[i]]=indices[i]
    
        def get_index_in_x(rec,total_size):
            index = 0
            for i in range(1, len(rec)):
                column = self.columns[i-1]
                val = rec[i]
                total_size /= len(self.domain_per_column[column])
                index += value_to_index_per_column[column][val]*total_size
            return int(index)
        print("Generating W and x") #TODO DEBUG
        #print(len(value_to_index_per_column['salary']), len(value_to_index_per_column['age']),total_size)
        cache = {}
        W = np.zeros((len(self.predicates), total_size))
        x = np.zeros(total_size)
        
        #generate W and x
        for i in range(len(results_by_query)):
            for rec in results_by_query[i]:
                index = None
                if rec in cache:
                    index = cache[rec]
                    W[i][index] = 1
                else:
                    index = get_index_in_x(rec, total_size)
                    cache[rec] = index
                    W[i][index] = 1
                    x[index] += 1
        self.W = W
        self.x = x
        print(W)
        print(x)