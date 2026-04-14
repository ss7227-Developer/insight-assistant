"""
app.py
Streamlit frontend for the AI-Powered Domain-Specific Insights Assistant.

Tabs:
  1. Chat with Documents  — query a domain, see structured insights + citations
  2. Ingest Documents     — upload files, build a FAISS index for a new/existing domain
  3. Evaluate Retrieval   — run precision@k / recall@k / MRR benchmarks
"""

import os
import tempfile

import streamlit as st

from pipelines.document_loader import load_documents
from pipelines.text_normalizer import normalize
from pipelines.chunker import chunk_documents
from core.vector_store import build_index, load_index, list_domains
from core.query_engine import create_chain, query
from core.explainability import build_citations, score_relevance
from core.embeddings import get_embeddings
from evaluation.benchmark_runner import run_benchmark

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Insights Assistant",
    page_icon="🔍",
    layout="wide",
)

# ── Session state ───────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chain" not in st.session_state:
    st.session_state.chain = None
if "active_domain" not in st.session_state:
    st.session_state.active_domain = None

# ── Header ──────────────────────────────────────────────────────────────────────
st.title("AI-Powered Domain-Specific Insights Assistant")
st.caption("RAG system powered by Amazon Bedrock embeddings + FAISS")

tab_chat, tab_ingest, tab_eval = st.tabs(
    ["💬 Chat with Documents", "📂 Ingest Documents", "📊 Evaluate Retrieval"]
)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════════════════════════════════════
with tab_chat:
    domains = list_domains()

    if not domains:
        st.info("No document indexes found. Go to the **Ingest Documents** tab to upload files first.")
    else:
        # Sidebar-style domain selector
        col_left, col_right = st.columns([1, 3])
        with col_left:
            selected_domain = st.selectbox("Select domain", domains, key="chat_domain")

            if st.button("Load domain", key="load_domain"):
                with st.spinner(f"Loading index for '{selected_domain}'..."):
                    try:
                        st.session_state.chain = create_chain(selected_domain)
                        st.session_state.active_domain = selected_domain
                        st.session_state.messages = []
                        st.success(f"Domain '{selected_domain}' loaded.")
                    except Exception as e:
                        st.error(f"Failed to load domain: {e}")

        with col_right:
            if st.session_state.active_domain:
                st.markdown(f"**Active domain:** `{st.session_state.active_domain}`")
            else:
                st.markdown("*No domain loaded yet. Click **Load domain**.*")

        st.divider()

        # Chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and msg.get("key_insights"):
                    with st.expander("Key Insights"):
                        for insight in msg["key_insights"]:
                            st.markdown(f"- {insight}")
                if msg["role"] == "assistant" and msg.get("citations"):
                    with st.expander("Sources"):
                        for c in msg["citations"]:
                            page = f" (page {c['page_num']})" if c.get("page_num") else ""
                            st.markdown(f"**{c['source']}**{page} — *{c['excerpt']}...*")

        # Chat input
        user_input = st.chat_input(
            "Ask a question about your documents...",
            disabled=(st.session_state.chain is None),
        )

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Retrieving and generating insights..."):
                    try:
                        result = query(st.session_state.chain, user_input)
                        answer = result["answer"]
                        key_insights = result["key_insights"]
                        confidence = result["confidence"]
                        source_docs = result["source_docs"]
                        citations = build_citations(source_docs)

                        # Confidence color
                        confidence_badge = {
                            "high": "🟢 High",
                            "medium": "🟡 Medium",
                            "low": "🔴 Low",
                        }.get(confidence, "⚪ Unknown")

                        st.markdown(answer)
                        st.caption(f"Confidence: {confidence_badge}")

                        if key_insights:
                            with st.expander("Key Insights"):
                                for insight in key_insights:
                                    st.markdown(f"- {insight}")

                        if citations:
                            with st.expander("Sources"):
                                for c in citations:
                                    page = f" (page {c['page_num']})" if c.get("page_num") else ""
                                    st.markdown(f"**{c['source']}**{page} — *{c['excerpt']}...*")

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "key_insights": key_insights,
                            "citations": citations,
                        })
                    except Exception as e:
                        st.error(f"Query failed: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — INGEST
# ════════════════════════════════════════════════════════════════════════════════
with tab_ingest:
    st.subheader("Upload Documents")
    st.markdown(
        "Supported formats: **.txt, .md, .pdf, .docx, .csv, .xlsx, .json**  \n"
        "Files are chunked and indexed into a domain-specific FAISS store."
    )

    domain_name = st.text_input(
        "Domain name",
        placeholder="e.g. finance, legal, hr-policies",
        help="Use a short, lowercase identifier. Existing domain indexes will be overwritten.",
    )

    uploaded_files = st.file_uploader(
        "Choose files",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx", "csv", "xlsx", "json"],
    )

    if st.button("Ingest & Index", disabled=(not domain_name or not uploaded_files)):
        progress = st.progress(0, text="Saving uploaded files...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Save uploads to temp dir
            for uf in uploaded_files:
                dest = os.path.join(tmp_dir, uf.name)
                with open(dest, "wb") as f:
                    f.write(uf.getbuffer())

            progress.progress(20, text="Loading documents...")
            docs = load_documents(tmp_dir, domain=domain_name)

            if not docs:
                st.error("No content could be extracted from the uploaded files.")
            else:
                progress.progress(40, text="Normalizing text...")
                docs = normalize(docs)

                progress.progress(60, text="Chunking documents...")
                chunks = chunk_documents(docs)

                progress.progress(80, text=f"Building FAISS index ({len(chunks)} chunks)...")
                try:
                    build_index(domain_name, chunks)
                    progress.progress(100, text="Done!")
                    st.success(
                        f"Ingested **{len(uploaded_files)} file(s)** into domain "
                        f"**'{domain_name}'** — **{len(chunks)} chunks** indexed."
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"Indexing failed: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — EVALUATE
# ════════════════════════════════════════════════════════════════════════════════
with tab_eval:
    st.subheader("Retrieval Benchmark")
    st.markdown(
        "Run precision@k, recall@k, MRR, and NDCG benchmarks against a ground-truth QA file. "
        "Edit `evaluation/ground_truth/sample_qa.json` to add your own questions."
    )

    eval_domains = list_domains()
    if not eval_domains:
        st.info("No indexes found. Ingest documents first.")
    else:
        eval_domain = st.selectbox("Domain", eval_domains, key="eval_domain")

        qa_file = st.text_input(
            "Ground-truth QA file path",
            value="evaluation/ground_truth/sample_qa.json",
        )

        k_slider = st.slider("k (number of retrieved docs)", min_value=1, max_value=10, value=5)

        if st.button("Run Benchmark"):
            if not os.path.exists(qa_file):
                st.error(f"QA file not found: {qa_file}")
            else:
                with st.spinner("Running benchmark..."):
                    try:
                        report = run_benchmark(domain=eval_domain, qa_path=qa_file, k=k_slider)

                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric(f"Precision@{k_slider}", f"{report['avg_precision_at_k']:.4f}")
                        col2.metric(f"Recall@{k_slider}", f"{report['avg_recall_at_k']:.4f}")
                        col3.metric("MRR", f"{report['avg_mrr']:.4f}")
                        col4.metric(f"NDCG@{k_slider}", f"{report['avg_ndcg_at_k']:.4f}")

                        st.divider()
                        st.markdown("**Per-question breakdown:**")

                        for r in report["per_question"]:
                            with st.expander(f"[{r['id']}] {r['question'][:80]}..."):
                                sub1, sub2, sub3, sub4 = st.columns(4)
                                sub1.metric(f"P@{k_slider}", r["precision_at_k"])
                                sub2.metric(f"R@{k_slider}", r["recall_at_k"])
                                sub3.metric("MRR", r["mrr"])
                                sub4.metric(f"NDCG@{k_slider}", r["ndcg_at_k"])
                                st.markdown(f"**Retrieved:** {r['retrieved_ids']}")
                                st.markdown(f"**Relevant:** {r['relevant_ids']}")

                    except Exception as e:
                        st.error(f"Benchmark failed: {e}")
