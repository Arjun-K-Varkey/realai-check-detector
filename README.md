[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

# RealAI Check – AI Misinformation Detector Prototype

An open-source tool to detect potential AI-generated text and fact-check claims in news articles. Built to support transparent, IFCN-aligned verification.

Part of the [RealAI Check](https://arjun-k-varkey.github.io/realaicheck.github.io/) independent fact-checking project focused on AI-generated misinformation.

## Features
- Detects if article text is likely AI-generated (using Hugging Face RoBERTa model)
- Extracts key factual claims
- Performs balanced web searches for supporting/challenging evidence
- Outputs structured JSON report
- Saves reports automatically

## How to Run (Easy Setup)

### 1. Clone or Download This Repo
```bash
git clone https://github.com/yourusername/realai-check-detector.git
cd realai-check-detector

### Sample Output
See a real analysis: [reports/misinfo_report_20260103_152833.json](reports/misinfo_report_20260103_152833.json)
