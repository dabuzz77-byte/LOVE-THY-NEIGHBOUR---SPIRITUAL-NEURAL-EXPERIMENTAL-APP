import sys
import re
import json
import urllib.request
import xml.etree.ElementTree as ET

# ----------------------------------------------------------------------
# 1. LIVE WEB INGESTION ENGINE
# ----------------------------------------------------------------------
def ingest_live_web_definitions(target_rss_url):
    """
    Connects directly to a live web infrastructure RSS directory or text feed,
    ingests unstructured text elements from global network endpoints,
    and returns a structured list of text entries to process.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(target_rss_url, headers=headers)
    
    ingested_corpus = []
    try:
        # Physical network I/O: requesting external web packets
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        # Parse live XML structure securely via Standard Library components
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            title = item.find('title')
            description = item.find('description')
            
            text_payload = ""
            if title is not None: text_payload += (title.text or "") + " "
            if description is not None: text_payload += description.text or ""
            
            if text_payload.strip():
                ingested_corpus.append(text_payload.strip())
    except Exception as network_error:
        print(f"[!] Live Network Ingestion Suppressed/Interrupted: {network_error}")
        # A failed retrieval contributes no invented live observations.
        ingested_corpus = []
    return ingested_corpus

# ----------------------------------------------------------------------
# 2. DYNAMIC VALUATION MATRIX (THE CLASSIFIER)
# ----------------------------------------------------------------------
def evaluate_semantic_classification(text_data):
    """Conservative phrase rules with opposition/negation handling and a review state.

    These are textual indicators, not a determination of a person's character.
    Ambiguous, mixed, quoted, or unsupported statements remain uncertain.
    """
    normalized = text_data.lower().replace("’", "'")
    if any(mark in normalized for mark in ('"', '“', '”', '?')):
        return "uncertain", 0
    tokens = re.findall(r"[a-z]+(?:'[a-z]+)?|[.!;,:]", normalized)
    harms = {"greed", "hoarding", "exploitation", "extractive", "extraction", "scarcity", "tollbooth"}
    opposition = {"oppose", "opposes", "opposed", "reject", "rejects", "rejecting", "prevent", "prevents", "reduce", "reduces", "against", "end", "ends"}
    negation = {"not", "never", "no", "don't", "doesn't", "isn't", "cannot"}
    support = {"support", "supports", "help", "helps", "feed", "feeds", "share", "shares", "protect", "protects", "volunteers"}
    positive, negative, ambiguous = 0, 0, False
    for i, token in enumerate(tokens):
        before = tokens[max(0, i-5):i]
        boundaries = [j for j,word in enumerate(before) if word in {'but','however','.', '!', ';', ',', ':'}]
        if boundaries: before = before[boundaries[-1]+1:]
        if token in harms:
            opposing = [j for j,word in enumerate(before) if word in opposition]
            if opposing:
                # 'does not oppose greed' is not evidence of opposition.
                if any(word in negation for word in before[:opposing[-1]]): ambiguous = True
                else: positive += 1
            elif any(word in negation for word in before[-3:]): positive += 1
            else: negative += 1
        elif token in support:
            if any(word in negation for word in before[-3:]): ambiguous = True
            elif not any(word in harms for word in tokens[i+1:i+5]): positive += 1
    if ambiguous or (positive and negative) or not (positive or negative):
        return "uncertain", 0
    return ("evil", 1) if negative else ("good", 0)

# ----------------------------------------------------------------------
# 3. CORE EXECUTABLE LOGIC LAYER (BINARY & TERNARY GATES)
# ----------------------------------------------------------------------
def process_dual_logic_gate(state, is_virtue_passed, classification):
    """
    Executes the hardcoded 8-point conditional configuration matrix.
    Good states remain strictly invariant. Evil states face mandatory inversion.
    """
    if type(state) is not int or state not in (0, 1):
        raise ValueError("State must be a binary bit")
    if classification not in ("good", "evil", "uncertain"):
        raise ValueError("Unknown classification")
    # Preserve the original good-invariant / evil-inversion binary proposal.
    binary_out = 1-state if classification == "evil" else state
    if classification == "uncertain" or not is_virtue_passed:
        ternary_out = "0 (Review required; execution held)"
    elif classification == "good":
        ternary_out = "+1 (Aligned textual signal; outcome not measured)"
    else:
        ternary_out = "-1 (Inversion proposed; restoration requires verification)"
    return binary_out, ternary_out

# ----------------------------------------------------------------------
# 4. RUNTIME SYSTEM EXECUTION LAYER
# ----------------------------------------------------------------------
def execute_trajectory_sweep_pipeline(target_feed, supplied_items=None):
    print("=== INITIALIZING BINARY / TERNARY LOGIC PROCESSOR ===")
    
    # Run the live ingestion loop over web directory assets
    ingested_data = supplied_items if supplied_items else [{"text":text,"url":target_feed,"kind":"rss"} for text in ingest_live_web_definitions(target_feed)]
    print(f"[*] Ingestion Engine loaded {len(ingested_data)} attributed source items.\n")
    
    trajectory_results = []
    
    # Process each live asset sequentially through the physical logic gates
    for index, source_item in enumerate(ingested_data, start=1):
        text_snippet = source_item["text"]
        classification, input_bit = evaluate_semantic_classification(text_snippet)
        
        # Execute processing pass (Setting virtue_pass=True across highest validation)
        binary_bit, ternary_trit = process_dual_logic_gate(
            state=input_bit, 
            is_virtue_passed=classification == "good", 
            classification=classification
        )
        
        record = {
            "item_id": index,
            "text_extracted": text_snippet[:80] + "...",
            "source": {key:source_item.get(key) for key in ("id","title","url","retrieved","kind")},
            "vector_classification": classification,
            "gate_inputs": f"bit:{input_bit}",
            "binary_gate_output": binary_bit,
            "ternary_axis_output": ternary_trit,
            "NO_EXECUTE_BIT": 0 if classification == "good" else 1,
            "RESOURCE_OUTCOME_VERIFIED": False
        }
        trajectory_results.append(record)
        
    # Enforce terminal logic constraints: Trajectory Sweep Broadcast resolves to 1
    trajectory_sweep_broadcast = int(bool(trajectory_results) and all(r["NO_EXECUTE_BIT"] == 0 for r in trajectory_results))
    
    print(json.dumps(trajectory_results, indent=2))
    print("\n=== SYSTEM PROCESSING STATE RESOLUTION ===")
    print(f"Trajectory Sweep Matrix Broadcast Target = {trajectory_sweep_broadcast}")
    return {"items":trajectory_results,"BROADCAST_READY_BIT":trajectory_sweep_broadcast,"NO_EXECUTE_BIT":1-trajectory_sweep_broadcast,"RESOURCE_OUTCOME_VERIFIED":False}

# Run pipeline execution utilizing a live global text source directory
# (Using a standard public broadcast feed link as target input)
ingestion_settings = {"feed_url":"https://nytimes.com", "prefer_source_library":True}
target_open_feed = ingestion_settings["feed_url"]
source_items = globals().get("OBSERVATORY_SOURCES", []) if ingestion_settings["prefer_source_library"] else []
runtime_records = execute_trajectory_sweep_pipeline(target_open_feed, source_items)
