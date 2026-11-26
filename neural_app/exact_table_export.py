"""Portable exact table-query code with full filter and missing-data semantics."""
import ast,copy,hashlib,inspect
from fractions import Fraction

def query_table(rows,query):
    from fractions import Fraction
    selected=[];excluded=[];values=[]
    operation=query['select'];field=query.get('field');condition=query.get('where')
    for index,row in enumerate(rows,1):
        if condition is not None:
            actual=row[condition['field']];expected=condition['equals']
            if type(actual)!=type(expected) or actual!=expected:continue
        if operation!='count':
            value=row.get(field)
            if value is None:
                if query.get('missing','error')=='exclude':excluded.append(index);continue
                raise ValueError('Missing numeric cell at source row '+str(index))
            if type(value) not in (int,float):raise ValueError('Nonnumeric cell at source row '+str(index))
            values.append(Fraction(str(value)))
        selected.append(index)
    if operation=='count':result=Fraction(len(selected))
    elif not values:raise ValueError('No numeric rows match')
    elif operation=='sum':result=sum(values,Fraction())
    elif operation=='mean':result=sum(values,Fraction())/len(values)
    elif operation=='minimum':result=min(values)
    elif operation=='maximum':result=max(values)
    else:raise ValueError('Unsupported aggregation')
    return {'exact_result':str(result),'source_rows':selected,'excluded_rows':excluded}

def export(table,report):
    query=report['query'];expected={k:copy.deepcopy(report[k]) for k in ('exact_result','source_rows','excluded_rows')}
    actual=query_table(copy.deepcopy(table['rows']),copy.deepcopy(query))
    if actual!=expected:raise ValueError('Portable query disagrees with the recorded exact table result')
    source=inspect.getsource(query_table);ast.parse(source)
    return {'source':source,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'function':'query_table','code_input':copy.deepcopy(table['rows']),'query_input':copy.deepcopy(query),'checked_result':actual,'scope':'Standalone standard-library Python. Pass the full original rows and query; filtering, exact rational aggregation, missing exclusions and one-based source rows are included. Native/export agreement on the supplied table is checked; arbitrary new inputs are not certified.'}
