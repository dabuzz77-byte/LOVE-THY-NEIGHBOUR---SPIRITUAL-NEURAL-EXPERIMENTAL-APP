"""Durable, independent AI conversations and atomic reset boundaries."""
import json
from pathlib import Path
import time
import uuid
from hub import database

PROVIDERS = ("llama", "gemini", "openai")


class ConversationStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with database(self.path) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS active_conversations(provider TEXT PRIMARY KEY, conversation_id TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, provider TEXT NOT NULL, title TEXT NOT NULL, created_at REAL, updated_at REAL)")
            db.execute("CREATE TABLE IF NOT EXISTS conversation_messages(id INTEGER PRIMARY KEY, conversation_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, wire_json TEXT, display_text TEXT NOT NULL, model TEXT, created_at REAL)")
            db.execute("CREATE INDEX IF NOT EXISTS conversation_order ON conversation_messages(conversation_id,id)")
            for provider in PROVIDERS:
                db.execute("INSERT OR IGNORE INTO active_conversations VALUES (?,?)", (provider,uuid.uuid4().hex))
                identity=db.execute("SELECT conversation_id FROM active_conversations WHERE provider=?",(provider,)).fetchone()[0]
                db.execute("INSERT OR IGNORE INTO conversations VALUES (?,?,?,?,?)",(identity,provider,"New conversation",time.time(),time.time()))

    @staticmethod
    def validate(provider):
        if provider not in PROVIDERS:raise ValueError("Unknown conversation provider")

    def snapshot(self, provider):
        self.validate(provider)
        with database(self.path) as db:
            db.execute("BEGIN")
            identity=db.execute("SELECT conversation_id FROM active_conversations WHERE provider=?",(provider,)).fetchone()[0]
            rows=db.execute("SELECT * FROM conversation_messages WHERE conversation_id=? ORDER BY id",(identity,)).fetchall()
        messages=[{"role":r["role"],"content":r["content"],"display":r["display_text"],
                   "wire":json.loads(r["wire_json"]) if r["wire_json"] else None,"model":r["model"]} for r in rows]
        return identity,messages

    def complete(self, provider, identity, prompt, reply, model, wire=None, display=None):
        """Commit a completed pair only if this is still the active conversation."""
        self.validate(provider)
        encoded=json.dumps(wire,ensure_ascii=False) if wire is not None else None
        with database(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            active=db.execute("SELECT conversation_id FROM active_conversations WHERE provider=?",(provider,)).fetchone()[0]
            if active!=identity:return False
            db.executemany("INSERT INTO conversation_messages(conversation_id,role,content,wire_json,display_text,model,created_at) VALUES (?,?,?,?,?,?,?)",[
                (identity,"user",prompt,None,prompt,model,time.time()),
                (identity,"assistant",reply,encoded,reply if display is None else display,model,time.time())])
            first=db.execute("SELECT content FROM conversation_messages WHERE conversation_id=? ORDER BY id LIMIT 1",(identity,)).fetchone()[0]
            db.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=?",(" ".join(first.split())[:70] or "Conversation",time.time(),identity))
        return True

    def reset(self, provider):
        self.validate(provider)
        identity=uuid.uuid4().hex
        with database(self.path) as db:
            db.execute("INSERT INTO conversations VALUES (?,?,?,?,?)",(identity,provider,"New conversation",time.time(),time.time()))
            db.execute("UPDATE active_conversations SET conversation_id=? WHERE provider=?",(identity,provider))
        return identity

    def list(self,provider):
        self.validate(provider)
        with database(self.path) as db:
            return [dict(r) for r in db.execute("SELECT c.*, (SELECT COUNT(*) FROM conversation_messages m WHERE m.conversation_id=c.id) AS message_count FROM conversations c WHERE provider=? ORDER BY updated_at DESC,id",(provider,))]

    def select(self,provider,identity):
        self.validate(provider)
        with database(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM conversations WHERE provider=? AND id=?",(provider,identity)).fetchone():
                raise ValueError("Conversation not found for this provider")
            db.execute("UPDATE active_conversations SET conversation_id=? WHERE provider=?",(identity,provider))


def transcript(messages):
    return "\n\n".join(("You" if m["role"]=="user" else (m.get("model") or "Assistant"))+"\n"+m.get("display",m["content"]) for m in messages)


def preview(prompt, state, history, compose):
    current=compose(prompt,state)
    if not history:return current
    return transcript(history)+"\n\nYou · next message\n"+current
