"""Hydrogen 1s and Slater-screened neutral-Si orbital cloud samples."""
import bisect,math
A0_NM=.0529177210903
SHELLS=[(1,0,13.7,2,'1s'),(2,0,9.85,2,'2s'),(2,1,9.85,6,'2p'),(3,0,4.15,2,'3s'),(3,1,4.15,2,'3p')]
def radial_table(n,l):
 xs=[i*36/2048 for i in range(2049)];pdf=[]
 for rho in xs:
  laguerre=1 if n-l-1==0 else 2-rho if (n,l)==(2,0) else 4-rho if (n,l)==(3,1) else .5*(rho*rho-6*rho+6)
  pdf.append(rho**(2*l+2)*math.exp(-rho)*laguerre**2)
 cdf=[0.]
 for i in range(1,len(xs)):cdf.append(cdf[-1]+(pdf[i]+pdf[i-1])*.5*(xs[i]-xs[i-1]))
 total=cdf[-1];return xs,[v/total for v in cdf]
TABLES={(n,l):radial_table(n,l) for n,l,_,_,_ in SHELLS}
def direction(rng,p_axis=None):
 z=rng.uniform(-1,1) if p_axis is None else (1 if rng.random()<.5 else -1)*rng.random()**(1/3);phi=rng.uniform(0,math.tau);r=math.sqrt(max(0,1-z*z));p=[r*math.cos(phi),r*math.sin(phi),z]
 if p_axis==0:p=[p[2],p[0],p[1]]
 elif p_axis==1:p=[p[0],p[2],p[1]]
 return p
class AtomicClouds:
 def sample(self,rng):
  radius=-A0_NM*.5*sum(math.log(max(1e-15,rng.random())) for _ in range(3));hydrogen={'element':'H','orbital':'1s','position_nm':[v*radius for v in direction(rng)],'radius_nm':radius,'radial_law':'P(r)=4r² exp(-2r/a0)/a0³','model':'Nonrelativistic hydrogen 1s probability model'}
  selected=rng.randrange(14);total=0
  for n,l,zeff,occupation,name in SHELLS:
   total+=occupation
   if selected<total:break
  xs,cdf=TABLES[(n,l)];u=rng.random();index=max(1,min(len(xs)-1,bisect.bisect_left(cdf,u)));fraction=(u-cdf[index-1])/max(1e-15,cdf[index]-cdf[index-1]);rho=xs[index-1]+fraction*(xs[index]-xs[index-1]);radius=rho*n*A0_NM/(2*zeff);axis=rng.randrange(2) if name=='3p' else None
  silicon={'element':'Si','orbital':name,'n':n,'l':l,'effective_charge':zeff,'occupation':occupation,'position_nm':[v*radius for v in direction(rng,axis)],'radius_nm':radius,'configuration':'[Ne] 3s² 3p²','model':'Independent-electron Slater-screened hydrogenic radial approximation; neutral-Si shell occupancy; 3p real-orbital illustration','radial_law':'rho^(2l+2) exp(-rho) [L_(n-l-1)^(2l+1)(rho)]²; rho=2 Z_eff r/(n a0)','first_ionization_reference_eV':8.1517}
  return {'hydrogen':hydrogen,'silicon':silicon,'display_radius_nm':.25,'provenance':'calculated-atomic-probability-model','bit_sampling':'Uniform sphere bit-point sampling remains separate from these overlaid atomic samples'}
