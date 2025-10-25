import os
import requests
import zipfile
import faiss
import numpy as np
import pickle
from ollama import AsyncClient
from lxml import etree
from bs4 import BeautifulSoup

async def build_index():
    client = AsyncClient()
    paragraphs = []

    # Simple English Wikipedia
    print("Downloading Simple English Wikipedia...")
    url = 'https://dumps.wikimedia.org/simplewiki/latest/simplewiki-latest-pages-articles.xml.bz2'
    r = requests.get(url)
    # Parse XML for paragraphs
    # This is simplified; in reality, parse the XML
    soup = BeautifulSoup(r.content, 'xml')
    for page in soup.find_all('page'):
        text = page.find('text').text
        pars = [p for p in text.split('\n') if len(p.split()) > 10 and len(p.split()) < 100]  # simple filter
        paragraphs.extend(pars[:10])  # limit

    # Gutenberg children's books - example URLs
    gutenberg_urls = [
        'https://www.gutenberg.org/files/148/148-0.txt',  # Alice in Wonderland
        'https://www.gutenberg.org/files/11/11-0.txt'     # Wizard of Oz
    ]
    for url in gutenberg_urls:
        r = requests.get(url)
        text = r.text
        pars = [p for p in text.split('\n\n') if len(p.split()) > 10 and len(p.split()) < 100]
        paragraphs.extend(pars[:50])

    # CommonLit - download CSV or something, but for now skip or use a small set

    # Limit to 1000 paragraphs
    paragraphs = paragraphs[:1000]

    print(f"Collected {len(paragraphs)} paragraphs")

    # Embed
    embeddings = []
    for i, p in enumerate(paragraphs):
        response = await client.embeddings(model='nomic-embed-text', prompt=p)
        emb = np.array(response['embedding'], dtype=np.float32)
        embeddings.append(emb)
        if i % 100 == 0:
            print(f"Embedded {i}")

    embeddings = np.array(embeddings)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    os.makedirs('models/faiss_index', exist_ok=True)
    faiss.write_index(index, 'models/faiss_index/index.faiss')
    with open('models/faiss_index/metadata.pkl', 'wb') as f:
        pickle.dump(paragraphs, f)

    print("Index built")

if __name__ == '__main__':
    import asyncio
    asyncio.run(build_index())
