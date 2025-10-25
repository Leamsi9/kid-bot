FROM nvidia/cuda:12.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3 python3-pip curl supervisor

RUN curl -fsSL https://ollama.ai/install.sh | sh

COPY requirements.txt .

RUN pip install -r requirements.txt

# Pull models
RUN ollama pull llama3.1:8b-instruct-q4_K_M && ollama pull nomic-embed-text

COPY . .

EXPOSE 8000

# Use supervisor to run ollama and app
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
