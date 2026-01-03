[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)

# RealAI Check – AI Misinformation Detector Prototype

An open-source tool to detect potential AI-generated text and fact-check claims in news articles. Built to support transparent, **IFCN-aligned** verification.

Part of the [RealAI Check](https://arjun-k-varkey.github.io/realaicheck.github.io/) independent fact-checking project focused on AI-generated misinformation and deepfakes.

## Features

- Detects if article text is likely AI-generated (Hugging Face RoBERTa model)
- Extracts key factual claims with strict filtering
- Performs balanced web searches for supporting and challenging evidence
- Outputs structured JSON report
- Automatically saves reports with timestamp

## How to Run (Easy Setup)

1.  **Clone or Download This Repo**
    ```bash
    git clone https://github.com/Arjun-K-Varkey/realai-check-detector.git
    cd realai-check-detector
    ```

2.  **Set Up Python Environment (Recommended)**
    ```bash
    python3 -m venv venv
    source venv/bin/activate    # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    
    Note: First run downloads large models (~1–2 GB). Only happens once!
    ```    

4.  **Run the Detector**
    ```bash
    python3 misinfo_detector.py
    
    Enter any news article URL when prompted.
    ```
    
5.  **Output**
    ```bash
    Full analysis printed in terminal
    
    Report saved as JSON in the reports/ folder
    Example filename: misinfo_report_20260103_152833.json
    ```
    **Sample Output**
    ```bash
    See a real analysis of the January 3, 2026 Venezuela/U.S. strikes event:
    reports/misinfo_report_20260103_152833.json
    ```
    **Example URLs to Test**
    ```bash
    BBC: https://www.bbc.com/news/articles/ce3ewqew4weo
    AP News (Venezuela event): https://apnews.com/article/venezuela-us-explosions-caracas-ca712a67aaefc30b1831f5bf0b50665e
    ```
