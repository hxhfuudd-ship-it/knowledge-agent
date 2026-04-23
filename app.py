"""Streamlit 主界面 - 展示所有模块"""
import json
import streamlit as st
from src.agent.core import Agent

st.set_page_config(page_title="知识库数据 Agent", page_icon="🤖", layout="wide")
st.title("🤖 知识库数据 Agent")
st.caption("用自然语言查询和分析数据 | Tool Use · RAG · Skills · MCP · Memory")

# 初始化
if "agent" not in st.session_state:
    st.session_state.agent = Agent()
if "messages" not in st.session_state:
    st.session_state.messages = []

agent = st.session_state.agent

# 侧边栏
with st.sidebar:
    tab1, tab2, tab3 = st.tabs(["💬 对话", "🧠 记忆", "📊 信息"])

    with tab1:
        if st.button("清空对话"):
            st.session_state.messages = []
            agent.reset()
            st.rerun()

        st.subheader("示例问题")
        examples = [
            "各部门有多少员工？",
            "上个月销售额是多少？",
            "哪个产品卖得最好？",
            "VIP客户主要分布在哪些城市？",
            "复购率是怎么计算的？",
            "生成一份销售月报",
            "帮我画个各部门人数的柱状图",
            "公司整体业绩怎么样？",
        ]
        for ex in examples:
            if st.button(ex, key=ex):
                st.session_state.pending_input = ex
                st.rerun()

    with tab2:
        st.subheader("记忆系统")
        stats = agent.get_memory_stats()
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
        st.code(
            "departments - 部门\n"
            "employees - 员工\n"
            "products - 产品\n"
            "customers - 客户\n"
            "orders - 订单\n"
            "order_items - 订单明细",
            language=None,
        )

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
                    st.markdown(f"**{tc['tool']}**")
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
                    st.markdown(f"**{tc['tool']}**")
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

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_result["response"] if final_result else "",
        "tool_calls": final_result["tool_calls"] if final_result else [],
        "skill": final_result.get("skill") if final_result else None,
        "skill_scores": skill_scores,
    })
