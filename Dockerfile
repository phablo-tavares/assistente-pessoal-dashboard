# 1. Use uma imagem base específica e leve para ter builds consistentes e menores
FROM python:latest

# 2. Defina variáveis de ambiente e o diretório de trabalho
ENV PYTHONUNBUFFERED=True
WORKDIR /app

# 3. Copie APENAS o arquivo de dependências para aproveitar o cache do Docker
COPY requirements.txt .

# 4. Instale as dependências. Este passo só será refeito se o requirements.txt mudar
RUN pip install -r requirements.txt

# 5. Copie TODO o resto do seu projeto para o diretório de trabalho
# Agora sua pasta local "app" estará em "/app/app" dentro do contêiner
COPY . .

# 6. Exponha a porta da aplicação
EXPOSE 8080

# 7. Defina o comando de entrada para iniciar a aplicação
# O caminho para o script agora é "app/app.py", relativo ao WORKDIR
ENTRYPOINT ["streamlit", "run", "app/app.py", "--server.port=8080", "--server.address=0.0.0.0"]