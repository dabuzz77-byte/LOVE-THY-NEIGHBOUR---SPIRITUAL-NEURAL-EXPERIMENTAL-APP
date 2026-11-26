"""Selectable engine attachments and non-destructive conversation context fitting."""
from copy import deepcopy
import json
import math

def context_choices(state):
    choices = [(key, key.replace('_', ' ').title()) for key in state if key != 'engines']
    choices += [('engine:' + row['engine'], row['engine']) for row in state.get('engines', [])]
    return choices

def compact(value, depth=0):
    if isinstance(value, str):
        return value if len(value) <= 600 else {'preview': value[:600], 'characters': len(value), 'abridged': True}
    if isinstance(value, dict):
        if depth >= 5:
            return {'keys': list(value)[:20], 'field_count': len(value), 'abridged': True}
        result = {k: compact(v, depth + 1) for k, v in list(value.items())[:24]}
        if len(value) > 24:
            result['_omitted_fields'] = len(value) - 24
        return result
    if isinstance(value, (list, tuple)):
        items = [compact(v, depth + 1) for v in value[:10]] if depth < 5 else []
        return items if len(items) == len(value) else {'items': items, 'item_count': len(value), 'abridged': True}
    return value

def select_context(state, selected=None, detail='compact'):
    allowed = set((key for key, _ in context_choices(state))) if selected is None else set(selected)
    result = {key: value for key, value in state.items() if key != 'engines' and key in allowed}
    engines = [row for row in state.get('engines', []) if 'engine:' + row['engine'] in allowed]
    if engines:
        result['engines'] = engines
    if detail == 'compact':
        result = compact(result)
        for key in list(result):
            encoded = json.dumps(result[key], ensure_ascii=False)
            if len(encoded) > 3500:
                result[key] = {'preview': encoded[:2800], 'characters': len(encoded), 'abridged': True}
    else:
        result = deepcopy(result)
    result['_context'] = {'detail': detail, 'selected_sections': sorted(allowed), 'scope': 'Outgoing attachment only; complete local results remain saved'}
    return result

def gemini_contents(prompt, state, history, compose):
    contents = [deepcopy(message.get('wire')) or {'role': 'model' if message['role'] == 'assistant' else 'user', 'parts': [{'text': message['content']}]} for message in history]
    contents.append({'role': 'user', 'parts': [{'text': compose(prompt, state)}]})
    return contents

def estimated_tokens(contents):
    return math.ceil(len(json.dumps(contents, ensure_ascii=False).encode('utf-8')) / 3)

def conversation_excerpts(messages, max_chars):
    if not messages or max_chars <= 0:
        return ''
    each = max(32, min(320, max_chars // len(messages)))
    lines = []
    for index, message in enumerate(messages):
        text = message['content']
        excerpt = text if len(text) <= each else text[:each // 2] + ' … ' + text[-each // 2:]
        lines.append(f"{index + 1}. {message['role']}: {excerpt}")
    text = '\n'.join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + '\n[Further excerpts omitted from this request.]'
    return 'Earlier saved conversation — excerpts, not complete turns:\n' + text + '\n[The complete conversation remains saved locally.]\n\nCurrent user message:\n'

def fit_context(prompt, state, history, budget, counter, compose):
    """Keep the current prompt intact; shorten only the outgoing history copy."""
    if type(budget) is not int or budget < 1:
        raise ValueError('Input token budget must be positive')
    total = counter(gemini_contents(prompt, state, history, compose))
    if total <= budget:
        return (prompt, history, {'input_tokens': total, 'recent_messages': len(history), 'excerpted_messages': 0, 'budget': budget})
    base = counter(gemini_contents(prompt, state, [], compose))
    if base > budget:
        raise ValueError(f'The new message and selected state need {base:,} tokens, above the {budget:,} input budget. Choose fewer engines, use Compact summaries, shorten this message, or increase the input budget. Saved history is unchanged.')
    keep = len(history)
    excerpt_chars = min(6000, max(0, (budget - base) // 2))
    while True:
        keep = max(0, keep // 4 * 2) if keep else 0
        older = history[:-keep] if keep else history
        recent = history[-keep:] if keep else []
        candidate = conversation_excerpts(older, excerpt_chars) + prompt
        total = counter(gemini_contents(candidate, state, recent, compose))
        if total <= budget:
            return (candidate, recent, {'input_tokens': total, 'recent_messages': len(recent), 'excerpted_messages': len(older) if excerpt_chars else 0, 'omitted_messages': len(older) if not excerpt_chars else 0, 'budget': budget, 'earlier_excerpt_characters': excerpt_chars})
        if not keep:
            if not excerpt_chars:
                raise ValueError('Token count changed while preparing input; please retry.')
            excerpt_chars //= 2
