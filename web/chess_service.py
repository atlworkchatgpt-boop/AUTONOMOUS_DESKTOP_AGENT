from __future__ import annotations
import json, random, sqlite3, time, uuid
from datetime import datetime, timezone
from pathlib import Path
import chess

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/"data"/"chess"
DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/"history.db"
LEVELS={"Easy":(1,.10,.35),"Medium":(2,.20,.12),"Hard":(2,.35,.05),"Expert":(3,.55,.02),"Master":(3,.90,0.0)}
VALUES={chess.PAWN:100,chess.KNIGHT:320,chess.BISHOP:330,chess.ROOK:500,chess.QUEEN:900,chess.KING:20000}

def _db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS games(game_id TEXT PRIMARY KEY, started_at TEXT, player_color TEXT, difficulty TEXT, moves TEXT, result TEXT, final_fen TEXT)")
    c.commit(); return c

def _save(g):
    c=_db(); c.execute("INSERT OR REPLACE INTO games VALUES(?,?,?,?,?,?,?)",(g.game_id,g.started_at,"black" if g.player_color==chess.BLACK else "white",g.difficulty,json.dumps(g.moves),g.result,g.board.fen())); c.commit(); c.close()

def evaluate(board):
    if board.is_checkmate(): return -1000000 if board.turn==chess.WHITE else 1000000
    score=0
    for p,v in VALUES.items(): score+=(len(board.pieces(p,chess.WHITE))-len(board.pieces(p,chess.BLACK)))*v
    return score

def minimax(board,depth,alpha,beta,maximizing,deadline):
    if time.monotonic()>=deadline or depth<=0 or board.is_game_over(): return evaluate(board),None
    moves=list(board.legal_moves)
    if not moves:return evaluate(board),None
    moves.sort(key=lambda m:(board.is_capture(m),board.gives_check(m)),reverse=True)
    best=moves[0]
    if maximizing:
        val=-10**9
        for m in moves:
            if time.monotonic()>=deadline:break
            board.push(m); s,_=minimax(board,depth-1,alpha,beta,False,deadline); board.pop()
            if s>val:val,best=s,m
            alpha=max(alpha,val)
            if beta<=alpha:break
        return val,best
    val=10**9
    for m in moves:
        if time.monotonic()>=deadline:break
        board.push(m); s,_=minimax(board,depth-1,alpha,beta,True,deadline); board.pop()
        if s<val:val,best=s,m
        beta=min(beta,val)
        if beta<=alpha:break
    return val,best

class ChessGame:
    def __init__(self,color="white",difficulty="Medium"):
        self.game_id=str(uuid.uuid4()); self.board=chess.Board(); self.player_color=chess.BLACK if str(color).lower()=="black" else chess.WHITE; self.difficulty=difficulty if difficulty in LEVELS else "Medium"; self.moves=[]; self.started_at=datetime.now(timezone.utc).isoformat(); self.result=None; _save(self)
    def status(self):
        if not self.board.is_game_over():return {"game_over":False,"result":None}
        out=self.board.outcome(); self.result=out.result() if out else self.board.result(); _save(self); return {"game_over":True,"result":self.result}
    def _push(self,move):
        san=self.board.san(move); self.board.push(move); self.moves.append({"uci":move.uci(),"san":san,"fen":self.board.fen()}); _save(self)
    def engine_move(self):
        if self.board.is_game_over():return None
        depth,seconds,randomness=LEVELS[self.difficulty]; legal=list(self.board.legal_moves)
        if not legal:return None
        _,move=minimax(self.board,depth,-10**9,10**9,self.board.turn==chess.WHITE,time.monotonic()+seconds)
        if move not in legal or (randomness and random.random()<randomness):move=random.choice(legal)
        self._push(move); return move

GAMES={}
def start_game(color="white",difficulty="Medium"):
    g=ChessGame(color,difficulty); GAMES[g.game_id]=g; return g
def get_game(game_id):
    g=GAMES.get(str(game_id))
    if g is None:raise KeyError("Chess game not found.")
    return g
def remove_game(game_id): GAMES.pop(str(game_id),None)
def make_player_move(game_id,move_text):
    g=get_game(game_id)
    if g.board.turn!=g.player_color:raise ValueError("It is not your turn.")
    try:m=chess.Move.from_uci(str(move_text).strip())
    except Exception:raise ValueError("Invalid chess move.")
    if m not in g.board.legal_moves:raise ValueError("Illegal chess move.")
    g._push(m); state=g.status()
    if state["game_over"]:return {"fen":g.board.fen(),"engine_move":None,**state}
    engine=g.engine_move(); state=g.status(); return {"fen":g.board.fen(),"engine_move":engine.uci() if engine else None,**state}

def list_history():
    c=_db(); rows=c.execute("SELECT * FROM games ORDER BY started_at DESC LIMIT 200").fetchall(); c.close()
    return [{**dict(r),"moves":json.loads(r["moves"] or "[]")} for r in rows]
def get_history(game_id):
    c=_db(); r=c.execute("SELECT * FROM games WHERE game_id=?",(game_id,)).fetchone(); c.close()
    if not r:return None
    d=dict(r); d["moves"]=json.loads(d["moves"] or "[]"); return d

def analyze_history(game_id):
    g=get_history(game_id)
    if not g:return None
    b=chess.Board(); notes=[]; captures=checks=mistakes=0
    for i,item in enumerate(g["moves"],1):
        try:m=chess.Move.from_uci(item["uci"])
        except Exception:continue
        if m not in b.legal_moves:continue
        before=evaluate(b); iscap=b.is_capture(m); gives=b.gives_check(m); san=b.san(m); b.push(m); after=evaluate(b)
        if iscap:captures+=1
        if gives:checks+=1
        mover_white=(i%2)==1; swing=(after-before) if mover_white else (before-after)
        tag="good"
        if swing<-300: tag="blunder"; mistakes+=1
        elif swing<-150: tag="mistake"; mistakes+=1
        elif iscap or gives: tag="active"
        notes.append(f"{i}. {san}: {tag}")
    text=f"Game {game_id}\nMoves: {len(g['moves'])}\nCaptures: {captures}\nChecks: {checks}\nMistakes/blunders: {mistakes}\nResult: {g.get('result') or 'In progress'}\n\n"+"\n".join(notes)
    return {"game":g,"captures":captures,"checks":checks,"mistakes":mistakes,"analysis_text":text}
