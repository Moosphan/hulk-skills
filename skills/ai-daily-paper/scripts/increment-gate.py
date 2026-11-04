#!/usr/bin/env python3
"""早晚报增量门禁：python3 increment-gate.py <morning_publish_iso> <items.json>
items.json: [{"title": "...", "time": "2026-11-04T09:12:00+08:00", "priority": "P0|P1|P2"}]
"""
import json, sys
from datetime import datetime
def main():
    pub = datetime.fromisoformat(sys.argv[1])
    items = json.load(open(sys.argv[2]))
    new = [i for i in items if datetime.fromisoformat(i["time"]) > pub]
    p0 = [i for i in new if i.get("priority") == "P0"]
    ok = len(new) >= 2 or bool(p0)
    print(json.dumps({"morningPublishAt": pub.isoformat(), "newItemCount": len(new),
                      "p0": [i["title"] for i in p0], "gatePassed": ok}, ensure_ascii=False, indent=1))
    sys.exit(0 if ok else 1)
main()
