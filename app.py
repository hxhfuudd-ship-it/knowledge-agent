"""Streamlit 主界面 - 展示所有模块"""
import json
import sqlite3
from pathlib import Path
import streamlit as st
from src.agent.core import Agent
from src import config
from src.path_utils import normalize_project_name, resolve_under, table_name_from_filename

st.set_page_config(page_title="知识库数据 Agent", page_icon="🤖", layout="wide")
st.title("🤖 知识库数据 Agent")
st.caption("用自然语言查询和分析数据 | Tool Use · RAG · Skills · MCP · Memory")

PROJECT_ROOT = Path(__file__).parent
DATABASES_DIR = PROJECT_ROOT / "data" / "databases"
DATABASES_DIR.mkdir(parents=True, exist_ok=True)


def get_projects():
    return sorted([f.stem for f in DATABASES_DIR.glob("*.db")])


def get_db_tables():
    db_path = PROJECT_ROOT / config.get("database.path", "data/databases/default.db")
    try:
        with sqlite3.connect(str(db_path)) as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            result = {}
            for (t,) in tables:
                cols = conn.execute("PRAGMA table_info([%s])" % t).fetchall()
                result[t] = [c[1] for c in cols]
            return result
    except sqlite3.Error:
        return {}



def render_trace(trace):
    if not trace:
        return
    summary = trace.get("summary", {})
    tokens = summary.get("tokens", {})
    with st.expander("📡 Trace / 性能"):
        cols = st.columns(4)
        cols[0].metric("总耗时", "%sms" % summary.get("total_duration_ms", 0))
        cols[1].metric("LLM 调用", summary.get("llm_calls", 0))
        cols[2].metric("工具调用", summary.get("tool_calls", 0))
        cols[3].metric("Token", tokens.get("total_tokens", 0))
        for event in trace.get("events", []):
            st.caption("%s · %s · %sms" % (event.get("type"), event.get("name"), event.get("duration_ms", 0)))
            metadata = event.get("metadata") or {}
            if metadata:
                st.json(metadata, expanded=False)


def render_tool_call(tc):
    st.markdown(f"**{tc['tool']}**")
    policy = tc.get("policy") or {}
    if policy:
        mode = "强制门禁" if policy.get("permission_enforced") else "仅审计"
        allowed = "允许" if policy.get("permission_allowed", True) else "拒绝"
        approved = "已审批" if policy.get("approved") else "未审批"
        st.caption(
            "Policy: risk=%s · %s · %s · %s" % (
                policy.get("risk_level", "unknown"),
                mode,
                allowed,
                approved,
            )
        )
        with st.expander("权限策略", expanded=False):
            st.json(policy, expanded=False)
    st.code(json.dumps(tc["input"], ensure_ascii=False, indent=2), language="json")
    output = tc["output"]
    if tc["tool"] == "rag_search" and "---" in output:
        st.markdown("**检索结果：**")
        for chunk in output.split("\n---\n"):
            chunk = chunk.strip()
            if chunk:
                st.info(chunk[:500])
    else:
        st.text(output[:500])
    st.divider()

# 初始化
if "agent" not in st.session_state:
    st.session_state.agent = Agent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_project" not in st.session_state:
    st.session_state.current_project = "default"

agent = st.session_state.agent

# 侧边栏
with st.sidebar:
    tab1, tab2, tab3 = st.tabs(["💬 对话", "🧠 记忆", "📊 信息"])

    with tab1:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            agent.reset()
            st.rerun()

        st.divider()
        st.caption("💡 试试这些问题")
        examples = [
            ("📊", "各部门有多少员工？"),
            ("💰", "上个月销售额是多少？"),
            ("🏆", "哪个产品卖得最好？"),
            ("🏙️", "VIP客户主要分布在哪些城市？"),
            ("🔄", "复购率是怎么计算的？"),
            ("📝", "生成一份销售月报"),
            ("📈", "帮我画个各部门人数的柱状图"),
            ("🎯", "公司整体业绩怎么样？"),
        ]
        for i in range(0, len(examples), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(examples):
                    icon, text = examples[i + j]
                    with col:
                        if st.button("%s %s" % (icon, text), key=text, use_container_width=True):
                            st.session_state.pending_input = text
                            st.rerun()

    with tab2:
        st.subheader("记忆系统")
        stats = agent.get_memory_stats()
        st.caption(f"当前 memory namespace: `{agent.memory_namespace}`")
        st.metric("短期记忆", f"{stats['short_term']} 条")
        st.metric("长期记忆", f"{stats['long_term']} 条")
        st.metric("情景记忆", f"{stats['episodic']} 条")

        st.divider()
        st.subheader("保存记忆")
        mem_input = st.text_input("输入要记住的内容")
        mem_cat = st.selectbox("类别", ["preference", "insight", "general"])
        if st.button("保存") and mem_input:
            agent.save_memory(mem_input, category=mem_cat)
            st.success("已保存")
            st.rerun()

        if stats["episodic"] > 0:
            st.divider()
            st.subheader("最近交互")
            for ep in agent.episodic.get_recent(5):
                st.text(f"[{ep['time_str']}]")
                st.caption(ep["summary"][:80])

    with tab3:
        st.subheader("项目管理")
        projects = get_projects()
        if not projects:
            projects = ["default"]

        selected = st.selectbox("当前项目", projects,
                                index=projects.index(st.session_state.current_project)
                                if st.session_state.current_project in projects else 0)
        if selected != st.session_state.current_project:
            st.session_state.current_project = selected
            config.set("database.path", "data/databases/%s.db" % selected)
            agent.set_memory_namespace(selected)
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("新建项目", placeholder="项目名")
            if st.button("创建") and new_name:
                try:
                    new_name = normalize_project_name(new_name)
                    new_db = resolve_under(DATABASES_DIR, "%s.db" % new_name)
                    if new_db.exists():
                        st.warning("项目已存在")
                    else:
                        sqlite3.connect(str(new_db)).close()
                        st.session_state.current_project = new_name
                        config.set("database.path", "data/databases/%s.db" % new_name)
                        agent.set_memory_namespace(new_name)
                        st.success("已创建: %s" % new_name)
                        st.rerun()
                except ValueError as e:
                    st.warning(str(e))
        with col2:
            if st.button("删除当前项目") and selected != "default":
                try:
                    safe_selected = normalize_project_name(selected)
                    db_file = resolve_under(DATABASES_DIR, "%s.db" % safe_selected)
                    if db_file.exists():
                        db_file.unlink()
                    st.session_state.current_project = "default"
                    config.set("database.path", "data/databases/default.db")
                    agent.set_memory_namespace("default")
                    st.rerun()
                except ValueError as e:
                    st.warning(str(e))
            elif selected == "default":
                st.caption("default 不可删除")

        st.divider()
        st.subheader("CSV 导入")
        uploaded_files = st.file_uploader("上传 CSV 文件（可多选）", type=["csv"], accept_multiple_files=True)
        if uploaded_files:
            import_mode = st.selectbox("导入模式", ["replace（覆盖）", "append（追加）"])
            mode = "replace" if "replace" in import_mode else "append"
            if st.button("导入全部（%d 个文件）" % len(uploaded_files)):
                import pandas as pd
                db_path = PROJECT_ROOT / config.get("database.path", "data/databases/default.db")
                success_count = 0
                for uf in uploaded_files:
                    table_name = table_name_from_filename(uf.name)
                    save_path = resolve_under(PROJECT_ROOT / "data", Path(uf.name).name)
                    save_path.write_bytes(uf.getvalue())
                    try:
                        df = pd.read_csv(str(save_path))
                        with sqlite3.connect(str(db_path)) as conn:
                            df.to_sql(table_name, conn, if_exists=mode, index=False)
                        st.success("%s → 表 %s（%d 行）" % (uf.name, table_name, len(df)))
                        success_count += 1
                    except Exception as e:
                        st.error("%s 导入失败: %s" % (uf.name, e))
                if success_count:
                    st.info("共导入 %d 个表" % success_count)
                    st.rerun()

        st.divider()
        st.subheader("已注册工具")
        for t in agent.registry.list_tools():
            st.code(t.name, language=None)

        st.divider()
        st.subheader("已注册 Skill")
        for s in agent.skill_registry.list_skills():
            st.markdown(f"**{s.name}**")
            st.caption(s.description[:50])

        st.divider()
        st.subheader("数据库表")
        tables = get_db_tables()
        if tables:
            for tname, cols in tables.items():
                st.markdown(f"**{tname}**")
                st.caption(", ".join(cols))
        else:
            st.info("数据库中没有表")

# 渲染历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg.get("skill") or msg.get("skill_scores"):
            with st.expander("🎯 Skill 路由详情"):
                if msg.get("skill"):
                    st.success(f"激活 Skill: **{msg['skill']}**")
                else:
                    st.info("未匹配到 Skill（通用对话模式）")
                if msg.get("skill_scores"):
                    for s in msg["skill_scores"]:
                        kw_tag = " ✅ 关键词命中" if s["keyword_match"] else ""
                        st.text(f"  {s['skill']:15s}  语义={s['embedding_score']:.3f}{kw_tag}")

        if msg.get("tool_calls"):
            with st.expander(f"🔧 工具调用 ({len(msg['tool_calls'])} 次)"):
                for tc in msg["tool_calls"]:
                    render_tool_call(tc)

        render_trace(msg.get("trace"))

# 处理输入
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("输入你的问题...") or pending

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        skill_scores = agent.skill_registry.match_with_scores(user_input)

        response_placeholder = st.empty()
        tool_events = []
        full_text = ""
        final_result = None

        for event in agent.chat_stream(user_input):
            if event["type"] == "token":
                full_text += event["content"]
                response_placeholder.markdown(full_text + "▌")
            elif event["type"] == "tool_call":
                tool_events.append(event)
            elif event["type"] in ("done", "error"):
                final_result = event["result"]

        if final_result:
            response_placeholder.markdown(final_result["response"])

        with st.expander("🎯 Skill 路由详情"):
            if final_result and final_result.get("skill"):
                st.success(f"激活 Skill: **{final_result['skill']}**")
            else:
                st.info("未匹配到 Skill（通用对话模式）")
            if skill_scores:
                for s in skill_scores:
                    kw_tag = " ✅ 关键词命中" if s["keyword_match"] else ""
                    st.text(f"  {s['skill']:15s}  语义={s['embedding_score']:.3f}{kw_tag}")

        if final_result and final_result["tool_calls"]:
            with st.expander(f"🔧 工具调用 ({len(final_result['tool_calls'])} 次)"):
                for tc in final_result["tool_calls"]:
                    render_tool_call(tc)

        if final_result:
            render_trace(final_result.get("trace"))

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_result["response"] if final_result else "",
        "tool_calls": final_result["tool_calls"] if final_result else [],
        "skill": final_result.get("skill") if final_result else None,
        "skill_scores": skill_scores,
        "trace": final_result.get("trace") if final_result else None,
    })
