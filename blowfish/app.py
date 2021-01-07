from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from blowfish import run_analysis

app = Flask(__name__)
api = Api(app)

#define constants
ATTRNAME = 'attrName'
ATTRTYPE = 'attrType'
WORKLOAD = 'workload'
THRESHOLDS = 'thresholds'
SENSITIVITY_SET = 'sensitivity_set'
RESULTS = 'results'


# info = {
#     "age": {
#         "type": "Numerical",
#         "policy": {
#             "template": "Line",
#             "graph": 7,
#             "bot": 0
#         }
#     },
#     "salary": {
#         "type": "Categorical",
#         "domain": [1,2,4,5,6,7,8,9,10,12,14],
#         "policy": {
#             "template": "Sensitivity",
#             "graph": [1,4,7,5,6,9],
#             "bot": 0
#         }
#     }
# }
####


class WorkloadForComparison(Resource):
    def post(self):
        data = request.get_json(force=True)
        predicates = data[WORKLOAD]
        attrname = data[ATTRNAME]
        results = []
        if data[ATTRTYPE] == 'Numerical':
            thresholds = data[THRESHOLDS]
            for val in thresholds:
                config = {
                    attrname: {
                        "type": "Numerical",
                        "policy":{
                            "template": "Line",
                            "graph": val,
                            "bot": 0
                        }
                    }
                }
                results.append(run_analysis(predicates,[attrname],config))
            return jsonify({RESULTS: results})
        else:
            print("TBD")
            return jsonify({RESULTS: results})


api.add_resource(WorkloadForComparison, '/')

if __name__ == '__main__':
    app.run(debug=True)