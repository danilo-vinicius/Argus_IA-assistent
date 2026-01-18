# Usa uma versão do Python que sabemos que funciona perfeitamente com IA
FROM python:3.11-slim

# Define variáveis de ambiente para o Python não gerar arquivos .pyc e logs aparecerem na hora
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define a pasta de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema operacional (necessário para PyAudio e compiladores básicos)
# O 'build-essential' resolve aquele erro de C++ que deu no seu Windows
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos e instala
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código para dentro do container
COPY . .

# Expõe a porta do Flask
EXPOSE 5000

# Comando para iniciar o Argus
CMD ["python", "app.py"]