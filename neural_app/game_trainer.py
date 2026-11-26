"""Native game-design trainer with finite level tests and engine concept references."""
import collections,time,threading
SOURCES=[{'title':'Unreal Engine 4.27 gameplay framework','url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-quick-reference?application_version=4.27','basis':'Actors and components; Pawn, Controller, GameMode and state separation.'},{'title':'UE4 Blueprint classes','url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprint-class?application_version=4.27','basis':'Reusable gameplay classes and event-driven behaviour.'},{'title':'Godot nodes and scenes','url':'https://docs.godotengine.org/en/stable/getting_started/step_by_step/nodes_and_scenes.html','basis':'Reusable scene trees composed of nodes.'},{'title':'Godot signals','url':'https://docs.godotengine.org/en/stable/getting_started/step_by_step/signals.html','basis':'Decoupled event communication between objects.'}]
LESSONS=[('Design brief','Define the player, objective, challenge, feedback and completion condition.'),('Scenes and entities','Separate world objects, reusable components and scene organisation.'),('Input and controllers','Map input to intentions and keep movement separate from game rules.'),('Rules and state','Model start, playing, victory, failure and restart states explicitly.'),('Events and visual logic','Trace event → condition → action → observed result.'),('Level design','Place obstacles and goals; test reachability and pacing.'),('Collision and physics','Distinguish grid collision from continuous physics, forces and rigid bodies.'),('Characters and animation','Connect animation state to movement and gameplay events.'),('Cameras and lighting','Compose readable scenes and preserve visual clarity.'),('Materials and assets','Track asset licences, memory use, formats and reusability.'),('Audio','Use music and sound to communicate events without obscuring essential feedback.'),('Interface and accessibility','Provide clear controls, readable contrast and alternatives to time pressure.'),('Game AI','Compare state machines, pathfinding and behaviour trees.'),('Saving and loading','Version scene data and validate it before use.'),('Multiplayer','Study authority, replication, latency and conflict handling.'),('Performance','Measure update cost, draw work, allocation and frame budgets.'),('Testing','Check invariants, unreachable goals, negative controls and repeatable inputs.'),('Packaging','Distinguish a native prototype JSON export from a built Unreal or Godot game.')]
DEFAULT=['############','#S.........#','#..###.....#','#......##..#','#..##......#','#.......#..#','#..........#','#........G.#','############']
def validate(rows):
 if not isinstance(rows,list) or not 3<=len(rows)<=32 or any(not isinstance(s,str) for s in rows):raise ValueError('Use 3–32 text rows')
 w=len(rows[0])
 if not 3<=w<=48 or any(len(s)!=w or set(s)-set('#.SG') for s in rows):raise ValueError('Use equal-width rows, 3–48 cells, and only # . S G')
 starts=[(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch=='S'];goals=[(x,y) for y,row in enumerate(rows) for x,ch in enumerate(row) if ch=='G']
 if len(starts)!=1 or len(goals)!=1:raise ValueError('Exactly one start S and goal G are required')
 queue=collections.deque([starts[0]]);parent={starts[0]:None}
 while queue:
  x,y=queue.popleft()
  for p in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
   a,b=p
   if 0<=a<w and 0<=b<len(rows) and rows[b][a]!='#' and p not in parent:parent[p]=(x,y);queue.append(p)
 path=[];p=goals[0]
 if p in parent:
  while p is not None:path.append(list(p));p=parent[p]
  path.reverse()
 return {'reachable':bool(path),'path':path,'steps':max(0,len(path)-1),'visited_cells':len(parent),'start':list(starts[0]),'goal':list(goals[0]),'width':w,'height':len(rows),'model':'Four-neighbour grid movement; walls block; reaching G wins.'}
class GameTrainer:
 def __init__(self):self.sequence=0;self.next_at=0;self.latest={};self.lock=threading.RLock()
 def view(self):
  with self.lock:return {'sources':SOURCES,'lessons':[{'title':a,'exercise':b} for a,b in LESSONS],'default_level':DEFAULT,'sequence':self.sequence,'latest':self.latest,'scope':'Native editable 2D prototype and deterministic tests informed by engine concepts. Unreal and Godot runtimes are not embedded.'}
 def tick(self,c):
  if time.monotonic()<self.next_at:return
  from .training_pace import interval
  self.next_at=time.monotonic()+interval(c);width=5+self.sequence%20;rows=['#'*width,'#S'+'.'*(width-4)+'G#','#'*width];positive=validate(rows);negative=validate(['#####','#S#G#','#####']);passed=positive['reachable'] and positive['steps']==width-3 and not negative['reachable']
  with self.lock:self.sequence+=1;self.latest={'passed':passed,'test':'Reachable goal plus blocked-goal negative control','path_steps':positive['steps']}
  c.bus.publish({'origin':'game-trainer','target':'all','kind':'stage-output','payload':{'sequence':self.sequence,'passed':passed,'path_steps':positive['steps'],'provenance':'native-game-rule-test','stochastic':False,'predefined_text':True}})
