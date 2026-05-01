Copy

FROM python:3.11-slim
 
# non-root user للأمان
RUN useradd -m botuser
 
WORKDIR /app
 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .
 
# تغيير الملكية
RUN chown -R botuser:botuser /app
 
USER botuser
 
CMD ["python", "main.py"]
 
