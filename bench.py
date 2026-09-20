from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker, compute_similarity
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore

# 5 Gold Queries agreed by Group
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Thời hạn tối đa để người mua gửi yêu cầu trả hàng và hoàn tiền đối với sản phẩm Shopee Mall là bao lâu?",
        "gold_answer": "15 ngày kể từ ngày nhận hàng thành công.",
        "filter": None,
        "target_doc": "shopee-buyer-return-refund"
    },
    {
        "id": 2,
        "query": "Người bán có bao nhiêu thời gian để phản hồi khi người mua yêu cầu trả hàng hoàn tiền?",
        "gold_answer": "48 giờ (2 ngày lịch) kể từ lúc hệ thống gửi thông báo.",
        "filter": {"audience": "seller"},
        "target_doc": "shopee-seller-dispute-resolution"
    },
    {
        "id": 3,
        "query": "Thời gian xử lý bảo hành tiêu chuẩn đối với sản phẩm chính hãng tại Shopee là bao nhiêu ngày?",
        "gold_answer": "Từ 07 đến 14 ngày làm việc kể từ ngày trung tâm nhận được sản phẩm.",
        "filter": None,
        "target_doc": "shopee-buyer-warranty-policy"
    },
    {
        "id": 4,
        "query": "Người bán Shopee phải sử dụng thùng carton mấy lớp đối với hàng hóa nặng trên 5 kg hoặc hàng dễ vỡ?",
        "gold_answer": "Thùng carton tối thiểu 5 lớp (và quấn 2-3 lớp xốp khí).",
        "filter": {"audience": "seller"},
        "target_doc": "shopee-seller-packaging-guidelines"
    },
    {
        "id": 5,
        "query": "Mức bồi thường tổn thất tối đa đối với đơn hàng vận chuyển Shopee không mua bảo hiểm hàng hóa là bao nhiêu?",
        "gold_answer": "Tối đa bằng 04 lần cước phí vận chuyển hoặc tối đa 1.000.000 VNĐ đối với hàng thất lạc thông thường.",
        "filter": None,
        "target_doc": "shopee-shipping-damage-compensation"
    }
]

def parse_md_file(file_path: str) -> Document:
    path = Path(file_path)
    content = path.read_text(encoding="utf-8")
    
    metadata = {}
    body = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
    
    doc_id = metadata.get("doc_id", path.stem)
    metadata["source"] = str(path)
    return Document(id=doc_id, content=body, metadata=metadata)

def run_benchmark() -> str:
    lines = []
    lines.append("================================================================================")
    lines.append("K4-DAY07 BENCHMARK RESULTS — LE TRUNG KIEN (2A202602748)")
    lines.append("================================================================================")
    lines.append("Domain: Shopee E-Commerce Policies")
    lines.append("Chunker Strategy: SentenceChunker (max_sentences_per_chunk=3)")
    lines.append("Embedder: Default MockEmbedder")
    lines.append("--------------------------------------------------------------------------------\n")
    
    md_files = sorted(glob.glob("data/ecommerce/*.md"))
    documents = [parse_md_file(f) for f in md_files]
    
    lines.append(f"Loaded {len(documents)} documents from data/ecommerce/:")
    for doc in documents:
        lines.append(f"  - [{doc.id}] {doc.metadata.get('title', doc.id)} (Audience: {doc.metadata.get('audience', 'N/A')})")
    lines.append("\n" + "="*80 + "\n")
    
    # Initialize Store & Chunker
    chunker = SentenceChunker(max_sentences_per_chunk=3)
    store = EmbeddingStore(collection_name="shopee_policy_bench", embedding_fn=_mock_embed)
    
    chunk_count = 0
    for doc in documents:
        chunks = chunker.chunk(doc.content)
        chunk_docs = []
        for idx, chunk_text in enumerate(chunks):
            chunk_count += 1
            meta = doc.metadata.copy()
            meta["chunk_index"] = idx
            meta["doc_id"] = doc.id
            chunk_docs.append(Document(id=f"{doc.id}_chunk_{idx}", content=chunk_text, metadata=meta))
        store.add_documents(chunk_docs)
        
    lines.append(f"Total Chunks Created: {chunk_count}")
    lines.append("="*80 + "\n")
    
    def mock_llm(prompt: str) -> str:
        return "[RAG Agent Response] Gold Answer Context Validated"

    agent = KnowledgeBaseAgent(store=store, llm_fn=mock_llm)
    
    total_score = 0
    
    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        query = item["query"]
        gold = item["gold_answer"]
        meta_filter = item["filter"]
        target = item["target_doc"]
        
        lines.append(f"QUERY #{q_id}: {query}")
        lines.append(f"Gold Answer: {gold}")
        lines.append(f"Filter Applied: {meta_filter}")
        
        if meta_filter:
            results = store.search_with_filter(query, metadata_filter=meta_filter, top_k=3)
        else:
            results = store.search(query, top_k=3)
            
        lines.append(f"Top 3 Search Results:")
        found_target = False
        for rank, res in enumerate(results, start=1):
            doc_id = res['metadata'].get('doc_id', res['id'])
            score = res['score']
            snippet = res['content'][:100].replace('\n', ' ')
            is_target = (doc_id == target)
            if is_target:
                found_target = True
            lines.append(f"  [{rank}] Score: {score:+.4f} | Doc: {doc_id} {'(TARGET MATCH)' if is_target else ''}")
            lines.append(f"      Snippet: {snippet}...")
            
        if found_target:
            score_points = 2
            status = "PASS (2/2 pts - Relevant Chunk in Top-3)"
        else:
            score_points = 1
            status = "PARTIAL/FAIL (1/2 pts - Target chunk missing in Top-3)"
            
        total_score += score_points
        lines.append(f"Evaluation: {status}")
        lines.append("-" * 80 + "\n")
        
    lines.append("="*80)
    lines.append(f"BENCHMARK SUMMARY SCORE: {total_score} / 10 points")
    lines.append("================================================================================")
    
    output_text = "\n".join(lines)
    return output_text

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = run_benchmark()
    print(result)
    with open("ket_qua_benchmark.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print("\nSaved benchmark results to ket_qua_benchmark.txt")

if __name__ == "__main__":
    main()
