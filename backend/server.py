"""
宇守信拼团自动化后端 — Flask + JSON 文件存储
API: /api/group/*   CRUD 拼团数据
启动: python3 server.py (默认端口 5188)
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join(os.path.dirname(__file__), "groups.json")
TZ = timezone(timedelta(hours=8))

# ── 数据层 ──────────────────────────────────────────

def load_groups():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return []

def save_groups(groups):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(groups, f, ensure_ascii=False, indent=2)

def now_str():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")

# ── API ──────────────────────────────────────────────

@app.route("/api/groups", methods=["GET"])
def list_groups():
    """列出所有团（管理员用）"""
    groups = load_groups()
    return jsonify({"ok": True, "groups": groups})


@app.route("/api/groups/active", methods=["GET"])
def active_groups():
    """获取当前进行中的团（首页展示）"""
    groups = load_groups()
    active = [g for g in groups if not g.get("completed")]
    active.sort(key=lambda x: x.get("joined", 0), reverse=True)
    return jsonify({
        "ok": True,
        "groups": [{
            "leader": g["leader"],
            "version": g["version"],
            "version_label": "📋财会版" if g.get("version") == "finance" else "📊老板版",
            "count": g.get("count", 1),
            "needed": max(0, 3 - g.get("count", 1)),
        } for g in active]
    })


@app.route("/api/group/query", methods=["GET"])
def query_group():
    """团长查进度"""
    leader = request.args.get("leader", "").strip()
    version = request.args.get("version", "")
    if not leader or not version:
        return jsonify({"ok": False, "msg": "参数不完整"})

    groups = load_groups()
    g = next((x for x in groups if x["leader"] == leader and x["version"] == version), None)
    if not g:
        return jsonify({"ok": False, "msg": "未找到该团"})

    count = g.get("count", 1)
    completed = g.get("completed", False)
    commission = 0
    if completed and count > 3:
        commission = (count - 3) * 10
    elif completed:
        commission = 0

    return jsonify({
        "ok": True,
        "group": {
            "leader": g["leader"],
            "version": g["version"],
            "count": count,
            "completed": completed,
            "commission": commission,
            "needed": 0 if completed else max(0, 3 - count),
            "progress_pct": min(100, int(count / 3 * 100)),
            "created_at": g.get("created_at", ""),
        }
    })


@app.route("/api/group/create", methods=["POST"])
def create_group():
    """管理员开团（团长付¥99后录入）"""
    data = request.get_json() or {}
    leader = data.get("leader", "").strip()
    version = data.get("version", "")

    if not leader or version not in ("finance", "boss"):
        return jsonify({"ok": False, "msg": "参数不完整"})

    groups = load_groups()
    existing = next((x for x in groups if x["leader"] == leader and x["version"] == version), None)
    if existing:
        return jsonify({"ok": False, "msg": f"团长 {leader} 的{version}团已存在"})

    g = {
        "leader": leader,
        "version": version,
        "count": 1,         # 团长自己算1人
        "completed": False,
        "commission": 0,
        "commission_paid": 0,   # 已结算佣金
        "refunded": False,      # 是否已退团长¥99
        "created_at": now_str(),
        "updated_at": now_str(),
        "members": [{"name": leader, "role": "leader", "joined_at": now_str()}],
    }
    groups.append(g)
    save_groups(groups)

    return jsonify({"ok": True, "group": g})


@app.route("/api/group/join", methods=["POST"])
def join_group():
    """团员参团（管理员收到¥99后录入）"""
    data = request.get_json() or {}
    leader = data.get("leader", "").strip()
    version = data.get("version", "")
    member_name = data.get("member", "").strip()

    if not leader or not version or not member_name:
        return jsonify({"ok": False, "msg": "参数不完整"})

    groups = load_groups()
    g = next((x for x in groups if x["leader"] == leader and x["version"] == version), None)
    if not g:
        return jsonify({"ok": False, "msg": "未找到该团"})

    g["count"] = g.get("count", 1) + 1
    g["updated_at"] = now_str()

    # 检查是否满3人
    if g["count"] >= 3 and not g.get("completed"):
        g["completed"] = True
        g["refunded"] = False  # 待退款

    # 第4人起累计佣金（¥10/单）
    if g["count"] > 3:
        g["commission"] = g.get("commission", 0) + 10

    if "members" not in g:
        g["members"] = []
    g["members"].append({"name": member_name, "role": "member", "joined_at": now_str()})

    save_groups(groups)
    return jsonify({"ok": True, "group": g})


@app.route("/api/group/refund", methods=["POST"])
def mark_refunded():
    """标记团长已退款¥99"""
    data = request.get_json() or {}
    leader = data.get("leader", "").strip()
    version = data.get("version", "")

    groups = load_groups()
    g = next((x for x in groups if x["leader"] == leader and x["version"] == version), None)
    if not g:
        return jsonify({"ok": False, "msg": "未找到该团"})
    g["refunded"] = True
    g["updated_at"] = now_str()
    save_groups(groups)
    return jsonify({"ok": True, "msg": "已标记退款"})


@app.route("/api/group/commission-pay", methods=["POST"])
def mark_commission_paid():
    """标记团长佣金已结算"""
    data = request.get_json() or {}
    leader = data.get("leader", "").strip()
    version = data.get("version", "")

    groups = load_groups()
    g = next((x for x in groups if x["leader"] == leader and x["version"] == version), None)
    if not g:
        return jsonify({"ok": False, "msg": "未找到该团"})
    g["commission_paid"] = g.get("commission", 0)
    g["updated_at"] = now_str()
    save_groups(groups)
    return jsonify({"ok": True, "msg": "佣金已结算"})


@app.route("/api/stats", methods=["GET"])
def stats():
    """统计看板"""
    groups = load_groups()
    total = len(groups)
    completed = sum(1 for g in groups if g.get("completed"))
    total_commission = sum(g.get("commission", 0) for g in groups)
    total_members = sum(g.get("count", 1) for g in groups)
    refunded = sum(1 for g in groups if g.get("refunded"))

    return jsonify({
        "ok": True,
        "stats": {
            "total_groups": total,
            "completed_groups": completed,
            "pending_groups": total - completed,
            "total_members": total_members,
            "total_commission": total_commission,
            "refunded_groups": refunded,
            "pending_refund": completed - refunded,
        }
    })


if __name__ == "__main__":
    print(f"🚀 宇守信拼团后端启动")
    print(f"   端口: 5188")
    print(f"   数据: {DATA_FILE}")
    print(f"   API:  http://localhost:5188/api/groups")
    app.run(host="0.0.0.0", port=5188, debug=True)
