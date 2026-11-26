"""Area-balanced summaries of the existing coarse weather grid, not climatology."""
import math

def summarize(rows,expected_grid):
 expected={(float(a),float(b)) for a,b in expected_grid};unique={}
 for row in rows:
  point=(row.get('lat'),row.get('lon'))
  if point in expected:unique[point]=row
 total=sum(math.cos(math.radians(a)) for a,b in expected)
 def group(selected):
  result={}
  for key in ('temperature_2m','relative_humidity_2m','surface_pressure','wind_speed_10m','cloud_cover','precipitation'):
   values=[]
   for (lat,lon),row in selected.items():
    value=row.get('values',{}).get(key)
    if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):values.append((value,math.cos(math.radians(lat))))
   if not values:continue
   weight=sum(w for v,w in values);ordered=sorted(values);acc=0;median=ordered[-1][0]
   for v,w in ordered:
    acc+=w
    if acc>=weight/2:median=v;break
   result[key]={'area_weighted_mean':sum(v*w for v,w in values)/weight,'area_weighted_median':median,'minimum':ordered[0][0],'maximum':ordered[-1][0],'valid_cells':len(values),'global_area_coverage_fraction':weight/total if total else 0}
  return result
 return {'method':'Cosine-latitude weighting of unique 30-degree cell-centre samples; missing cells excluded, not filled with zero. Coarse snapshot approximation, not a climate normal or a dense sensor survey.','expected_cells':len(expected),'received_cells':len(unique),'global':group(unique),'north':group({p:r for p,r in unique.items() if p[0]>=0}),'south':group({p:r for p,r in unique.items() if p[0]<0}),'source_times':sorted({r['time'] for r in unique.values() if r.get('time')}),'units':{'temperature_2m':'°C','relative_humidity_2m':'%','surface_pressure':'hPa','wind_speed_10m':'m/s','cloud_cover':'%','precipitation':'mm / preceding hour'},'data_kind':'modelled weather estimates; source-reported values'}
