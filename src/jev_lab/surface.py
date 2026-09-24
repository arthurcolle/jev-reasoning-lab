import json, time, hashlib
from typesafe_sdk import TypeSafeClient, Noul, Choice, Score

class Receipt:
    def __init__(self, domain, kind, subject, result, confidence, latency_ms, usage):
        self.schema = "dsco.jev_decide.v1"
        self.domain, self.kind, self.subject = domain, kind, subject
        self.result, self.confidence = result, confidence
        self.latency_ms, self.usage = latency_ms, usage
        self.ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    def to_json(self): return json.dumps(self.__dict__)

class JevDecisionSurface:
    """Typed decision helper with an in-memory receipt list; not a capability gate or durable audit log."""
    def __init__(self, model="jev-1.13.0"):
        self.model = model
        self.ledger = []   # append-only receipt log

    def _call(self, questions, state):
        from .safety import require_live
        require_live()
        t0 = time.time()
        with TypeSafeClient() as c:
            r = c.system_one(state=state, questions=questions, model=self.model)
        return r, (time.time() - t0) * 1000

    def _record(self, domain, kind, subject, result, conf, lat, usage):
        rc = Receipt(domain, kind, subject, result, conf, round(lat, 1),
                     {"in": usage.input_tokens, "out": usage.output_tokens})
        self.ledger.append(rc)
        return rc

    def decide_bool(self, domain, subject, instruction, threshold=0.5):
        r, lat = self._call({"q": Noul(instructions=instruction)}, state=subject)
        p = r.nouls["q"].noul
        rc = self._record(domain, "bool", subject[:60], p >= threshold, p, lat, r.usage)
        return (p >= threshold), p, rc

    def decide_score(self, domain, subject, instruction, levels):
        labels = [str(x) for x in levels]
        r, lat = self._call({"q": Score(instructions=instruction, criteria=labels)}, state=subject)
        sc = r.scores["q"]
        rc = self._record(domain, "score", subject[:60], round(sc.score, 2), sc.confidence, lat, r.usage)
        return sc.score, sc.confidence, rc

    def decide_choice(self, domain, subject, instruction, options):
        crit = {o: None for o in options}
        r, lat = self._call({"q": Choice(instructions=instruction, criteria=crit)}, state=subject)
        ch = r.choices["q"]
        rc = self._record(domain, "choice", subject[:60], ch.choice, ch.confidence, lat, r.usage)
        return ch.choice, ch.confidence, rc

    def batch_bool(self, domain, subjects, instruction_fn, threshold=0.5):
        """Many subjects, one System One call. Returns {index: (bool, p)}."""
        NL = chr(10)
        state = "Items:" + NL + NL.join(f"[{i}] {s}" for i, s in enumerate(subjects))
        qs = {f"q_{i}": Noul(instructions=f"For item {i}: {instruction_fn(i, subjects[i])}") for i in range(len(subjects))}
        r, lat = self._call(qs, state)
        out = {i: (r.nouls[f"q_{i}"].noul >= threshold, r.nouls[f"q_{i}"].noul) for i in range(len(subjects))}
        self._record(domain, "batch_bool", f"{len(subjects)} items", len(subjects), None, lat, r.usage)
        return out
