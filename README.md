# 🤖 Local RAG AI Assistant with Microsoft Foundry Local

> **Tamamen çevrimdışı çalışan, tarayıcı tabanlı bir Soru-Cevap asistanı.**
> Retrieval-Augmented Generation (RAG) ve Microsoft Foundry Local ile güçlendirilmiştir.
> Bulut yok, API anahtarı yok, internet gerekmez.

A fully offline, browser-based Q&A assistant powered by **Retrieval-Augmented Generation (RAG)** and **Microsoft Foundry Local**, built with **Python**. No cloud, no API keys, no internet required after initial model download.

---

## 📋 İçindekiler / Table of Contents

- [Özellikler / Features](#-özellikler--features)
- [Sistem Mimarisi / System Architecture](#-sistem-mimarisi--system-architecture)
- [RAG Pipeline Akışı / RAG Pipeline Flow](#-rag-pipeline-akışı--rag-pipeline-flow)
- [Bileşen Mimarisi / Component Architecture](#-bileşen-mimarisi--component-architecture)
- [Veri Akışı / Data Flow](#-veri-akışı--data-flow)
- [Teknoloji Yığını / Tech Stack](#-teknoloji-yığını--tech-stack)
- [Ön Koşullar / Prerequisites](#-ön-koşullar--prerequisites)
- [Hızlı Başlangıç / Quick Start](#-hızlı-başlangıç--quick-start)
- [Proje Yapısı / Project Structure](#-proje-yapısı--project-structure)
- [API Referansı / API Reference](#-api-referansı--api-reference)
- [Sunum Metni / Presentation Script](#-sunum-metni--presentation-script)
- [Lisans / License](#-lisans--license)

---

## ✨ Özellikler / Features

| Özellik | Açıklama |
|---------|----------|
| 🔒 **Tamamen Çevrimdışı** | İlk model indirme sonrası internet gerektirmez |
| 🧠 **Yerel LLM** | Phi-3.5 Mini — Foundry Local SDK (CPU/NPU hızlandırma) |
| 📄 **Doküman İndeksleme** | Markdown/Text/PDF dosyalarını SQLite vektör deposuna aktarır |
| 🔍 **TF-IDF Arama** | Ters dizin + kosinüs benzerliği ile hızlı, şeffaf arama |
| 💬 **Akış Yanıt (Streaming)** | Server-Sent Events ile gerçek zamanlı token-token yanıt |
| 📱 **Responsive Arayüz** | Glassmorphic karanlık tema, mobil uyumlu |
| 📤 **Çalışma Zamanı Yükleme** | Sunucuyu yeniden başlatmadan yeni doküman ekleme |
| 📚 **Kaynak Atıfları** | Her yanıtta belge adı ve relevance % gösterir |

---

## 🏗️ Sistem Mimarisi / System Architecture

Aşağıdaki diyagram, sistemin uçtan uca genel mimarisini gösterir:

```mermaid
graph TB
    subgraph CLIENT["🖥️ İstemci Katmanı (Client Layer)"]
        BROWSER["🌐 Web Tarayıcı<br/>index.html"]
    end

    subgraph SERVER["⚙️ Sunucu Katmanı (Server Layer)"]
        FASTAPI["🚀 FastAPI Server<br/>server.py<br/>Port: 3000"]
        STATIC["📁 Static Files<br/>public/"]
    end

    subgraph RAG_PIPELINE["🧠 RAG Pipeline Katmanı"]
        CHAT_ENGINE["💬 Chat Engine<br/>chat_engine.py"]
        PROMPTS["📝 Prompt Builder<br/>prompts.py"]
        VECTOR_STORE["🔍 Vector Store<br/>vector_store.py"]
    end

    subgraph DATA_LAYER["💾 Veri Katmanı (Data Layer)"]
        SQLITE[("🗄️ SQLite DB<br/>data/rag.db<br/>WAL Mode")]
        DOCS["📂 docs/<br/>Markdown, Text & PDF"]
    end

    subgraph INGESTION["📥 Veri Alım Katmanı"]
        INGEST["🔄 Ingest Script<br/>ingest.py"]
        CHUNKER["✂️ Chunker<br/>chunker.py"]
        CONFIG["⚙️ Config<br/>config.py"]
    end

    subgraph AI_RUNTIME["🤖 Yapay Zeka Çalışma Zamanı"]
        FOUNDRY["Microsoft Foundry Local<br/>On-Device Runtime"]
        PHI["Phi-3.5 Mini<br/>SLM Model"]
    end

    BROWSER <-->|"HTTP/SSE"| FASTAPI
    FASTAPI --> STATIC
    FASTAPI --> CHAT_ENGINE
    CHAT_ENGINE --> PROMPTS
    CHAT_ENGINE --> VECTOR_STORE
    VECTOR_STORE <-->|"SQL Read/Write"| SQLITE
    CHAT_ENGINE <-->|"OpenAI Compatible API<br/>stream=True"| FOUNDRY
    FOUNDRY --> PHI

    DOCS --> INGEST
    INGEST --> CHUNKER
    CHUNKER -->|"Chunked + TF-IDF"| VECTOR_STORE
    CONFIG -.->|"Settings"| INGEST
    CONFIG -.->|"Settings"| FASTAPI
    CONFIG -.->|"Settings"| CHAT_ENGINE

    classDef clientStyle fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#fff
    classDef serverStyle fill:#16213e,stroke:#0f3460,stroke-width:2px,color:#fff
    classDef ragStyle fill:#0f3460,stroke:#533483,stroke-width:2px,color:#fff
    classDef dataStyle fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#fff
    classDef aiStyle fill:#533483,stroke:#e94560,stroke-width:2px,color:#fff

    class CLIENT clientStyle
    class SERVER serverStyle
    class RAG_PIPELINE ragStyle
    class DATA_LAYER dataStyle
    class AI_RUNTIME aiStyle
```

---

## 🔄 RAG Pipeline Akışı / RAG Pipeline Flow

Bir kullanıcı sorusu sorulduğunda RAG pipeline'ının adım adım işleyişi:

```mermaid
sequenceDiagram
    actor User as 👤 Kullanıcı
    participant Browser as 🌐 Tarayıcı
    participant Server as 🚀 FastAPI
    participant ChatEngine as 💬 Chat Engine
    participant VectorStore as 🔍 Vector Store
    participant SQLite as 🗄️ SQLite
    participant Foundry as 🤖 Foundry Local
    participant Phi as 🧠 Phi-3.5 Mini

    User->>Browser: Soru yazar
    Browser->>Server: POST /api/chat {query}
    Server->>ChatEngine: chat(query)

    Note over ChatEngine: Adım 1: Retrieval (Arama)
    ChatEngine->>VectorStore: search(query, top_k=3)
    VectorStore->>VectorStore: term_frequency(query)
    VectorStore->>SQLite: Inverted Index ile adayları bul
    SQLite-->>VectorStore: Aday chunk'lar
    VectorStore->>VectorStore: cosine_similarity() hesapla
    VectorStore-->>ChatEngine: En benzer 3 chunk

    Note over ChatEngine: Adım 2: Augment (Zenginleştirme)
    ChatEngine->>ChatEngine: build_prompt_messages()
    Note right of ChatEngine: System Prompt<br/>+ Conversation History<br/>+ Retrieved Context<br/>+ User Question

    Note over ChatEngine: Adım 3: Generate (Üretim)
    ChatEngine->>Foundry: chat.completions.create(stream=True)
    Foundry->>Phi: Inference
    loop Token-by-token streaming
        Phi-->>Foundry: Token
        Foundry-->>ChatEngine: Token
        ChatEngine-->>Server: {type: "token", content}
        Server-->>Browser: SSE: data: {...}
        Browser-->>User: Anlık metin görüntüleme
    end

    ChatEngine-->>Server: {type: "sources", sources: [...]}
    Server-->>Browser: SSE: kaynak bilgileri
    ChatEngine-->>Server: {type: "done"}
    Server-->>Browser: SSE: tamamlandı
```

---

## 🧩 Bileşen Mimarisi / Component Architecture

Her Python modülünün sorumluluğu ve birbirleriyle ilişkisi:

```mermaid
graph LR
    subgraph CORE["Çekirdek Modüller"]
        CONFIG["⚙️ config.py<br/>───────────<br/>• Port, host<br/>• Model adı<br/>• Chunk boyutu<br/>• Overlap<br/>• Top-K<br/>• Dosya yolları"]

        CHUNKER["✂️ chunker.py<br/>───────────<br/>• YAML front-matter<br/>  parse<br/>• Overlap pencereli<br/>  metin parçalama<br/>• Doküman işleme"]

        VECTOR["🔍 vector_store.py<br/>───────────<br/>• TF-IDF hesaplama<br/>• Kosinüs benzerliği<br/>• SQLite CRUD<br/>• Inverted index<br/>• In-memory cache"]

        PROMPTS["📝 prompts.py<br/>───────────<br/>• System prompt<br/>• Bağlam enjeksiyonu<br/>• Sohbet geçmişi<br/>  yönetimi"]

        CHAT["💬 chat_engine.py<br/>───────────<br/>• RAG orkestrasyon<br/>• Streaming yanıt<br/>• Fallback modu<br/>• Geçmiş yönetimi"]
    end

    subgraph ENTRY["Giriş Noktaları"]
        SERVER["🚀 server.py<br/>───────────<br/>• FastAPI app<br/>• SSE endpoints<br/>• Model lifecycle<br/>• Upload API<br/>• SDK patch"]

        INGEST["📥 ingest.py<br/>───────────<br/>• docs/ tarama<br/>• Batch indeksleme<br/>• İstatistik raporlama"]
    end

    CONFIG --> SERVER
    CONFIG --> INGEST
    CONFIG --> CHAT
    CONFIG --> VECTOR
    CONFIG --> CHUNKER
    CHUNKER --> INGEST
    VECTOR --> INGEST
    VECTOR --> CHAT
    PROMPTS --> CHAT
    CHAT --> SERVER
    CHUNKER --> SERVER
    VECTOR --> SERVER
```

---

## 📊 Veri Akışı / Data Flow

### Doküman İndeksleme Süreci (Ingestion Flow)

```mermaid
flowchart LR
    A["📂 docs/<br/>Markdown/Text/PDF<br/>Dosyaları"] -->|"Dosya oku"| B["📄 Ham Metin"]
    B -->|"parse_front_matter()"| C["📋 Metadata<br/>+ İçerik"]
    C -->|"chunk_text()<br/>200 kelime, 25 overlap"| D["✂️ Parçalar<br/>(Chunks)"]
    D -->|"term_frequency()"| E["📊 TF-IDF<br/>Vektörleri"]
    E -->|"INSERT INTO documents"| F[("🗄️ SQLite<br/>rag.db")]

    style A fill:#e94560,color:#fff
    style F fill:#533483,color:#fff
```

### Sorgu İşleme Süreci (Query Flow)

```mermaid
flowchart LR
    Q["❓ Kullanıcı Sorusu"] -->|"term_frequency()"| QV["📊 Sorgu<br/>TF Vektörü"]
    QV -->|"Inverted Index"| CANDS["🎯 Aday<br/>Chunk'lar"]
    CANDS -->|"cosine_similarity()"| RANKED["📈 Sıralanmış<br/>Sonuçlar"]
    RANKED -->|"top_k = 3"| TOP["🏆 En İyi 3<br/>Chunk"]
    TOP -->|"build_prompt()"| PROMPT["📝 LLM<br/>Prompt"]
    PROMPT -->|"stream=True"| ANSWER["💬 Akış<br/>Yanıt"]

    style Q fill:#e94560,color:#fff
    style ANSWER fill:#533483,color:#fff
```

### SQLite Veritabanı Şeması

```mermaid
erDiagram
    DOCUMENTS {
        INTEGER id PK "AUTO INCREMENT"
        TEXT doc_id "Doküman tanımlayıcı"
        TEXT title "Doküman başlığı"
        TEXT category "Kategori (varsayılan: General)"
        INTEGER chunk_index "Parça sıra numarası"
        TEXT content "Parça içeriği"
        TEXT tf_json "TF-IDF vektörü (JSON)"
    }
```

---

## 🛠️ Teknoloji Yığını / Tech Stack

```mermaid
graph TB
    subgraph FRONTEND["Frontend"]
        HTML["HTML5 + CSS3 + Vanilla JS"]
        SSE["Server-Sent Events"]
        GLASS["Glassmorphic Dark UI"]
    end

    subgraph BACKEND["Backend"]
        PYTHON["Python 3.10+"]
        FASTAPI["FastAPI ≥ 0.110"]
        UVICORN["Uvicorn ASGI"]
    end

    subgraph AI["AI / ML"]
        FOUNDRY_SDK["Foundry Local SDK ≥ 0.5"]
        OPENAI_SDK["OpenAI Python SDK ≥ 1.14"]
        PHI_MODEL["Phi-3.5 Mini (SLM)"]
        TFIDF["TF-IDF (Custom)"]
    end

    subgraph STORAGE["Storage"]
        SQLITE_DB["SQLite 3 (WAL Mode)"]
        FS["Local Filesystem"]
    end

    FRONTEND --> BACKEND
    BACKEND --> AI
    BACKEND --> STORAGE

    classDef front fill:#e94560,stroke:#fff,color:#fff
    classDef back fill:#0f3460,stroke:#fff,color:#fff
    classDef ai fill:#533483,stroke:#fff,color:#fff
    classDef store fill:#1a1a2e,stroke:#e94560,color:#fff

    class FRONTEND front
    class BACKEND back
    class AI ai
    class STORAGE store
```

---

## ⚙️ Ön Koşullar / Prerequisites

- **Python 3.10+**: [İndir / Download](https://www.python.org/)
- **Microsoft Foundry Local**: Cihaz üzerinde yapay zeka çalışma zamanı
  - Windows: `winget install Microsoft.FoundryLocal`
  - macOS/Linux: [Resmi dökümentasyon](https://learn.microsoft.com/en-us/ai/foundry-local/)

---

## 🚀 Hızlı Başlangıç / Quick Start

```bash
# 1. Bağımlılıkları kur / Install dependencies
pip install -r requirements.txt

# 2. Dokümanları vektör deposuna indeksle / Ingest documents
python src/ingest.py

# 3. Sunucuyu başlat / Start the server
python src/server.py
```

Tarayıcıda aç / Open in browser → [http://127.0.0.1:3000](http://127.0.0.1:3000)

> **Not / Note**: İlk çalıştırmada Phi-3.5 Mini modeli (~2 GB) indirilir. Sonraki çalıştırmalar önbellekten yüklenir.

---

## 📂 Proje Yapısı / Project Structure

```
📦 Local RAG AI Assistant
├── 📂 docs/                    # Kaynak dokümanlar (markdown/text/pdf)
│   ├── 01-rag-introduction.md
│   ├── 02-foundry-local-guide.md
│   ├── 03-embeddings-and-vectors.md
│   ├── 04-sqlite-guide.md
│   └── 05-prompt-engineering.md
├── 📂 data/                    # SQLite veritabanı (otomatik oluşturulur)
│   └── rag.db
├── 📂 public/                  # Frontend (tek HTML dosyası)
│   └── index.html
├── 📂 src/                     # Python kaynak kodları
│   ├── config.py               # Yapılandırma sabitleri
│   ├── chunker.py              # Overlap pencereli metin parçalama
│   ├── vector_store.py         # TF-IDF + SQLite vektör deposu
│   ├── prompts.py              # Sistem istemi mühendisliği
│   ├── chat_engine.py          # RAG pipeline orkestrasyonu
│   ├── ingest.py               # Doküman alım betiği
│   └── server.py               # FastAPI sunucu + API rotaları
├── requirements.txt            # Python bağımlılıkları
└── README.md                   # Bu dosya
```

---

## 📡 API Referansı / API Reference

| Method | Endpoint | Açıklama | Yanıt Tipi |
|--------|----------|----------|------------|
| `GET` | `/api/status` | Model yükleme durumu (SSE stream) | `text/event-stream` |
| `POST` | `/api/chat` | Soru sor, RAG yanıtı al (SSE stream) | `text/event-stream` |
| `POST` | `/api/upload` | Yeni doküman yükle ve indeksle | `application/json` |
| `GET` | `/api/documents` | İndekslenmiş doküman listesi | `application/json` |
| `POST` | `/api/clear` | Sohbet geçmişini temizle | `application/json` |

### SSE Event Tipleri

```json
// Token akışı
{"type": "token", "content": "Merhaba, bu bir "}

// Kaynak bilgileri
{"type": "sources", "sources": [{"title": "...", "docId": "...", "score": 0.85, "preview": "..."}]}

// Tamamlandı
{"type": "done"}
```

---

## 📄 Dokümanlarınızı Ekleme / Adding Your Own Documents

1. `.md`, `.txt` veya `.pdf` dosyalarını `docs/` klasörüne koyun
2. `python src/ingest.py` ile indeksleyin
3. `python src/server.py` ile sunucuyu başlatın

---

## 📜 Lisans / License

MIT
