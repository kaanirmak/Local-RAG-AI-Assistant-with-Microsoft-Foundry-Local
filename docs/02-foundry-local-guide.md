---
title: Microsoft Foundry Local Guide
category: Setup
id: doc-foundry-local
---

# Microsoft Foundry Local

Foundry Local is a lightweight runtime from Microsoft that downloads, manages, and serves language models entirely on your device. No cloud account, no API keys, no outbound network calls after the initial model download.

## Key Features

- **No GPU Required**: Runs on CPU or NPU, making it accessible on standard laptops and desktops.
- **Native SDK Bindings**: In-process inference with no HTTP round-trips to a local server.
- **Automatic Model Management**: Downloads, caches, and loads models automatically.
- **Hardware-Optimised Variant Selection**: The SDK picks the best variant for your hardware (GPU, NPU, or CPU).
- **Real-time Progress Callbacks**: Ideal for building loading UIs that show download and initialisation progress.

## Installation

### Windows
```
winget install Microsoft.FoundryLocal
```

### Python SDK
```
pip install foundry-local-sdk openai
```

### Node.js SDK
```
npm install foundry-local-sdk
```

## Supported Models

Foundry Local provides a curated catalog of optimized models including:
- **Phi-3.5 Mini**: A compact 3.8B parameter model ideal for Q&A and chat tasks
- **Phi-1.5**: A smaller model for quick responses on constrained devices
- Various embedding models for vectorisation tasks

## How It Works

1. The SDK initializes and connects to the local Foundry runtime
2. It discovers available models in the local catalog
3. If a model isn't cached, it downloads it (one-time operation)
4. The model is loaded into memory for inference
5. Your application sends prompts and receives completions — all locally

## Use Cases

- Offline AI assistants for field workers
- Privacy-sensitive document processing
- Edge computing and IoT applications
- Educational tools without internet dependency
- Local code generation and analysis
