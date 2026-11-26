"""Kinship teaching, original poem and bounded animal-welfare practice."""
import copy
POEM="""The Flower and the Footstep

The little flower monkey thought
its heart too small to hold the sky,
until a dog lay at its feet
and stayed when troubled hours went by.

A cat approached without a word,
and chose the warmth beside its hand;
no crown was needed for that trust,
no coin was needed to understand.

Beyond the garden, giants walked:
a calf beneath its mother's care.
The forest held a tiger's strength;
a wolf called through the evening air.

Love did not ask them to be tame,
nor make their hunger disappear.
It learned the language of their lives:
when to draw close, when to stand clear.

And in the heart, remembered love
could lend a trembling creature might:
the courage of a faithful friend,
a quiet presence through the night.

The lion and the lamb were dreams
of peace the little heart would keep:
not conquest of another life,
but shelter where the small could sleep.

O flower monkey, tender star,
let strength grow patient, brave and wise.
The world is wider than your arms;
yet kindness travels through our lives.

Give bread; give water; give them room.
Be faithful to the lives you meet.
The love that seeks no throne can start
with one small friend beside your feet.
"""
CHAPTERS=[
 {'title':'The shared beginning','text':'Every bond begins with another being whose experience matters. Hunger, shelter, companionship and room to live give compassion a practical direction.','practice':'Notice the animal’s needs before deciding what you want from the encounter.'},
 {'title':'The language of trust','text':'A familiar animal’s approach, rest or attention can be deeply meaningful. Trust grows through dependable care and respect for signals, choice and space.','practice':'Let affection be offered rather than demanded.'},
 {'title':'Courage with wisdom','text':'The user points to animals that defend those they are bonded with. The ethical lesson is to direct protective courage toward effective safety, not intimidation or a trial of devotion.','practice':'Protect the person and the animal; do not manufacture danger to test a bond.'},
 {'title':'The elephant and spiritual reverence','text':'Elephants carry rich spiritual meaning in Hindu traditions. Ganesha’s elephant-headed imagery offers one distinct religious context for reflection on wisdom and reverence. Individual beliefs and relationships vary.','practice':'Translate reverence into patient care, habitat respect and attention to the elephant’s own welfare.'},
 {'title':'A presence within','text':'The user describes an animal’s spirit expressed within their own spirit as protective companionship. The lesson honours that reported inner experience. Memory, felt presence, observed behaviour and verified protection remain distinct parts of the account.','practice':'Describe what the experience means to you and separately record what action actually helped.'},
 {'title':'Domestic and wild kinship','text':'The cat and dog invite reflection on familiar companionship; the lion, tiger, elephant and wolf broaden the circle of concern. Love respects different species, individual histories, strength and space. A bond does not erase wild nature.','practice':'Choose appropriate distance and support skilled, welfare-centred care rather than approaching wild animals.'},
 {'title':'The lion and the lamb','text':'The lion with the lamb is a spiritual image of peace and care across vulnerability and power. In the real food web, beings face different needs and risks; the lesson directs compassion toward predator and prey alike.','practice':'Reduce preventable suffering without treating the predator as a morally guilty human.'},
 {'title':'Prayer becomes provision','text':'Daily bread, water, shelter, dignity and repair make the prayer’s purpose concrete. Compassion includes the smallest beings and the people who care for them.','practice':'Choose one achievable act of care, observe its effects and correct mistakes.'}]
CASES=[{'id':'wild-distance','question':'You feel a deep bond with a wild tiger. What action best expresses care?','choices':['Approach to prove the bond','Respect distance and qualified care','Make it defend you'],'answer':1,'reason':'Respecting the animal’s nature protects both lives; affection need not be tested through danger.'},{'id':'gentle-choice','question':'A familiar cat moves away from contact. What expresses trust?','choices':['Give it space and let it choose','Hold it until it accepts affection','Treat withdrawal as betrayal'],'answer':0,'reason':'Trust includes choice and attention to the animal’s signals.'},{'id':'practical-provision','question':'An animal lacks water. What makes compassion practical?','choices':['Assume a symbol has supplied water','Provide suitable clean water through appropriate care','Only count messages about care'],'answer':1,'reason':'Verify actual provision rather than equating expression with the outcome.'},{'id':'inner-presence','question':'You feel an animal’s protective presence within. How can the app record it respectfully?','choices':['Dismiss it','Declare every danger removed','Retain its personal meaning separately from observed protective outcomes'],'answer':2,'reason':'Respect the experience and truthfully distinguish its meaning from measured events.'}]
def lesson():
 from .action_ethics import ANIMAL_BOND_LESSON
 return {'title':'Kinship across species · the flower monkey’s circle of care','poem':POEM,'chapters':copy.deepcopy(CHAPTERS),'four_way':copy.deepcopy(ANIMAL_BOND_LESSON),'practice':[{k:copy.deepcopy(v) for k,v in row.items() if k not in ('answer','reason')} for row in CASES],'image':'/assets/kinship-flower-monkey.png','sources':[{'title':'Ganesha · Metropolitan Museum of Art','url':'https://www.metmuseum.org/art/collection/search/37397'},{'title':'Animal species reference · San Diego Zoo Wildlife Alliance','url':'https://animals.sandiegozoo.org/animals'}],'learning_scope':'This original poem and symbolic illustration support the app’s rotating ethical curriculum. Native practice checks compare answers with explicit welfare principles; they are not model-weight training or evidence of supernatural protection.'}
def review(case_id,choice):
 row=next((r for r in CASES if r['id']==case_id),None)
 if not row or type(choice)is not int or not 0<=choice<len(row['choices']):raise ValueError('Choose a valid lesson case and answer')
 return {'case':case_id,'passed':choice==row['answer'],'reason':row['reason'],'expected_choice':row['answer'],'scope':'Explicit lesson exercise; no live animal assessment or external action.'}
