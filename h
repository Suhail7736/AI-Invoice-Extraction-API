[1mdiff --git a/app/main.py b/app/main.py[m
[1mindex 07a4c96..ae3bcaa 100644[m
[1m--- a/app/main.py[m
[1m+++ b/app/main.py[m
[36m@@ -11,9 +11,7 @@[m [mfrom .extractor import extract_invoice[m
 from .schemas import InvoiceResponse[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # Environment Configuration[m
[31m-# --------------------------------------------------[m
 [m
 load_dotenv(override=True)[m
 API_KEY = os.getenv("GEMINI_API_KEY")[m
[36m@@ -25,18 +23,14 @@[m [mif not API_KEY:[m
     )[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # Gemini Client[m
[31m-# --------------------------------------------------[m
 [m
 client = genai.Client([m
     api_key=API_KEY[m
 )[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # FastAPI Application[m
[31m-# --------------------------------------------------[m
 [m
 app = FastAPI([m
     title="AI Invoice Extraction API",[m
[36m@@ -48,9 +42,7 @@[m [mapp = FastAPI([m
 )[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # Root Endpoint[m
[31m-# --------------------------------------------------[m
 [m
 @app.get("/")[m
 def root():[m
[36m@@ -60,9 +52,7 @@[m [mdef root():[m
     }[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # Health Check[m
[31m-# --------------------------------------------------[m
 [m
 @app.get("/health")[m
 def health():[m
[36m@@ -72,9 +62,7 @@[m [mdef health():[m
     }[m
 [m
 [m
[31m-# --------------------------------------------------[m
 # Invoice Extraction[m
[31m-# --------------------------------------------------[m
 [m
 @app.post([m
     "/extract-invoice",[m
