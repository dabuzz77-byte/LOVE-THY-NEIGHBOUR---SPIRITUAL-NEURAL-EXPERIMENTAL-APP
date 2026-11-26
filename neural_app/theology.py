"""Source-linked comparative theology and explicit Gnostic bridge proposals."""
import hashlib
import json

THEMES = {
 'unity': {'title':'God, unity and revelation',
  'islam':'Qur’an 4:171 affirms divine unity and identifies Jesus as a messenger and word from God, while rejecting a triadic formulation.',
  'christianity':'John 1:1–14 presents the Word in relation to God and describes the Word becoming flesh.',
  'encounter':'Both passages place Jesus and divine revelation at the centre of discussion. Their accounts of divine identity differ.',
  'bridge':'Explore how inward understanding, humility and compassionate conduct can deepen the encounter with revelation while stating doctrinal differences clearly.',
  'sources':[{'title':'Qur’an 4:171','url':'https://legacy.quran.com/04/171'},{'title':'John 1:1–14','url':'https://www.biblegateway.com/passage/?search=John+1%3A1-14&version=NRSVUE'}]},
 'light': {'title':'Light, inward knowledge and awakening',
  'islam':'The Qur’an’s Light Verse uses a lamp, glass and an olive tree to describe divine light.',
  'christianity':'John’s prologue joins life, light and the Word.',
  'encounter':'Light offers a shared vocabulary for guidance, although each tradition gives it a particular theological setting.',
  'bridge':'Read illumination alongside the search for gnosis: let inward understanding become mercy, attentiveness and care for life.',
  'sources':[{'title':'Qur’an 24:35','url':'https://legacy.quran.com/24/35'},{'title':'John 1','url':'https://www.biblegateway.com/passage/?search=John+1&version=NRSVUE'},{'title':'Gospel of Thomas collection, including saying 3','url':'https://gnosis.org/naghamm/gosthom.html'}]},
 'care': {'title':'Mercy, conduct and vulnerable life',
  'islam':'Islamic teaching gives mercy, charitable responsibility and accountability important roles.',
  'christianity':'Christian teaching places love of neighbour, mercy and care for people in need at the heart of conduct.',
  'encounter':'A discussion can move from declarations to specific acts of mercy, repair and responsibility.',
  'bridge':'Use the app’s Bread of Life principle to ask how insight changes treatment of vulnerable beings, including both predator and prey.',
  'sources':[{'title':'Qur’an 90:12–18','url':'https://quran.com/90/12-18'},{'title':'Matthew 25:31–46','url':'https://www.biblegateway.com/passage/?search=Matthew+25%3A31-46&version=NRSVUE'}]},
 'gnosis': {'title':'Faith, knowledge and the soul’s journey',
  'islam':'Muslim traditions discuss faith, understanding and guidance through their own scriptural and interpretive practices.',
  'christianity':'Christian traditions discuss faith, knowledge of God and transformation through distinct theological practices.',
  'encounter':'The question for study is how belief, understanding and conduct interact in each teaching.',
  'bridge':'Follow the Gnostic bridge developed in this app: receive the teaching, seek inward understanding and embody care, with participation chosen by the learner.',
  'sources':[{'title':'Gospel of Thomas collection','url':'https://gnosis.org/naghamm/gosthom.html'},{'title':'Proverbs 3:13–18','url':'https://www.sefaria.org/Proverbs.3.13-18?lang2=en&with=all'}]},
}


def compare(body):
    topic=body.get('topic','unity').removeprefix('theology_')
    if topic not in THEMES:raise ValueError('Choose unity, light, care or gnosis')
    records=body.get('records',[])
    if not isinstance(records,list) or len(records)>10:raise ValueError('Use at most ten bibliographic records')
    checked=[]
    for row in records:
        if not isinstance(row,dict) or not isinstance(row.get('title'),str) or len(row['title'])>500:raise ValueError('Invalid research title')
        url=row.get('url','')
        if not isinstance(url,str) or len(url)>1000 or (url and not url.startswith('https://')):raise ValueError('Use HTTPS source links')
        checked.append({'title':row['title'],'url':url,'doi':str(row.get('doi',''))[:200],'reading_status':'bibliographic discovery; full text not automatically reviewed'})
    theme=THEMES[topic]
    plan=[{'step':1,'action':'Read both primary passages in context and record each position accurately.'},
          {'step':2,'action':'Name shared concerns and the exact doctrinal disagreement.'},
          {'step':3,'action':theme['bridge']},
          {'step':4,'action':'Choose an act of mercy, care or repair and examine its consequences.'},
          {'step':5,'action':'Review the usefulness of the synthesis explicitly; retain sources and revise the proposal.'}]
    digest=hashlib.sha256(json.dumps({'topic':topic,'records':checked},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    words=' '.join(v['title'].lower() for v in checked)
    hits=sum(k in words for k in ['islam','christian','gnos','theolog','religio','faith','mercy','revelation'])
    return {'status':'COMPLETE','topic':topic,'title':theme['title'],'comparison':{k:theme[k] for k in ['islam','christianity','encounter']},
            'gnostic_bridge_proposal':theme['bridge'],'transition_plan':plan,'primary_sources':theme['sources'],'research_records':checked,
            'source_digest':digest,'routing_features':[min(1,hits/4)*2-1,min(1,len(checked)/3)*2-1],
            'method':'Source-linked, rule-based comparative synthesis, with a neural routing signal and explicit usefulness learning. Bibliographic titles identify material to read; they are not substituted for full-text debate analysis.',
            'compact_public':{'format':'neural-theology-context-v1','topic':topic,'title':theme['title'],'direction':'Gnostic insight expressed through mercy, understanding and care','plan_steps':len(plan),'research_record_count':len(checked),'digest':digest}}
