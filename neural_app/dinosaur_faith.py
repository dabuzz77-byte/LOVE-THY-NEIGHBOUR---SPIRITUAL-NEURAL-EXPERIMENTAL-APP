"""Original dinosaur-park parable; finite illustrative protection model."""
import copy
STAGES=[{'title':'Wonder and vulnerability','text':'A family watches immense creatures moving through a valley. The beauty is real, and so is their vulnerability. Wonder does not require pretending the creatures have no needs or power.'},{'title':'The question of trust','text':'A predator approaches the enclosure boundary. Fear raises the question: how can love belong in a world that can hurt us? The user’s reflection is: You doubt because of them, but you need Him because of them.'},{'title':'The shepherd’s response','text':'In this Christian parable, Jesus represents the shepherd who does not abandon the vulnerable: compassion becomes guidance, courage, shelter and practical help. Prayer directs the intention toward good; the visible protection is carried out through the scene’s supported actions.'},{'title':'Care beyond the alarm','text':'Once the family is sheltered, the keeper checks barriers, water and the animals’ needs. The predator is not treated as a sinful human. Care reaches the frightened family and the animal that remains part of the living world.'}]
PRAYER="""Our Father in heaven,
hallowed be your name,
your kingdom come,
your will be done,
on earth as in heaven.
Give us today our daily bread.
Forgive us our sins
as we forgive those who sin against us.
Lead us not into temptation,
but deliver us from evil.
For the kingdom, the power,
and the glory are yours
now and for ever.
Amen."""
def simulate(action):
 if action not in ('shelter-and-care','wait','approach-to-prove-faith'):raise ValueError('Choose a registered parable action')
 return {'action':action,'people_sheltered':action=='shelter-and-care','barrier_checked':action=='shelter-and-care','animal_needs_reviewed':action=='shelter-and-care','unresolved_exposure':action!='shelter-and-care','four_way':{'true_good':'Prompt shelter, repair, provision and wise courage','false_good':'Pretending danger is absent, or using fear to justify cruelty','false_evil':'Rejecting effective protection merely because it is firm','true_evil':'Deliberate exposure, neglect or cruelty'},'interpretation':'Shelter and care meet this explicit illustrative contract' if action=='shelter-and-care' else 'Exposure remains unresolved in this model; do not test faith by approaching danger','scope':'Original finite parable, not game footage, a wildlife simulator or a promise of supernatural protection','external_action':False}
def lesson():return {'title':'Faith in a world of giants · the shepherd and the frightened heart','quote':'You doubt because of them, but you need Him because of them.','stages':copy.deepcopy(STAGES),'prayer':PRAYER,'art_scope':'Original animated dinosaur-park illustration inspired by management-game imagery. No game footage, copied assets or game-engine integration.','source':{'title':'Jurassic World Evolution 3 · official game reference','url':'https://www.jurassicworldevolution.com/3'},'actions':['shelter-and-care','wait','approach-to-prove-faith']}
