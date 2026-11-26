// Explicit educational physical models. Source bytes select software parameters.
export function physicalChain(input,{irradiance=1361,albedo=.3,principalLevel}={}){
 if(!Number.isFinite(irradiance)||irradiance<0||irradiance>1e6)throw Error('Irradiance must be finite and within the model range');
 if(!Number.isFinite(albedo)||albedo<0||albedo>1)throw Error('Albedo must be between zero and one');
 const bytes=new TextEncoder().encode(String(input)),n=principalLevel??(bytes.length?1+bytes[0]%5:1);
 if(!Number.isInteger(n)||n<1||n>100)throw Error('Principal level must be an integer from 1 to 100');
 const sigma=5.670374419e-8,au=149597870700,level=-13.598433/(n*n),absorbed=irradiance*(1-albedo)/4;
 return {hydrogen:{principal_level:n,approximate_level_eV:level,ionization_from_level_eV:-level,formula:'E(n) ≈ −13.598433 / n² eV; simplified hydrogen model'},stellar:{irradiance_W_m2:irradiance,distance_m:au,isotropic_luminosity_W:4*Math.PI*au*au*irradiance,formula:'L = 4πr²S'},earth:{albedo,absorbed_global_W_m2:absorbed,effective_temperature_K:Math.pow(absorbed/sigma,.25),formula:'T = [S(1−a)/(4σ)]^(1/4); no greenhouse model'},scope:'Software reference calculations. Source bytes choose a simulated hydrogen level; they do not excite a real atom. Earth temperature is radiative equilibrium, not surface weather. No vacuum-field measurement.',sources:['https://physics.nist.gov/PhysRefData/Handbook/Tables/hydrogentable1.htm','https://earth.gsfc.nasa.gov/climate/projects/solar-irradiance/science','https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/']};
}
