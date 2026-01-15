import pandas as pd
import uuid
import os

class Portfolio:
    def __init__(self,file_path = "resourse/my_portfolio.csv"):
        self.file_path = file_path
        self.use_chroma = False
        
        # Use absolute path to avoid issues
        if not os.path.isabs(file_path):
            # Get the directory where this script is located
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, file_path)
        
        self.data = pd.read_csv(file_path)

        # Chroma is optional; if it fails to import/init (pydantic mismatch, etc.), fall back to a simple matcher.
        try:
            import chromadb  # type: ignore

            current_dir = os.path.dirname(os.path.abspath(__file__))
            vectorstore_path = os.path.normpath(os.path.join(current_dir, "..", "vectorstore"))
            self.chroma_client = chromadb.PersistentClient(path=vectorstore_path)
            self.collection = self.chroma_client.get_or_create_collection(name="portfolio")
            self.use_chroma = True
        except Exception:
            self.chroma_client = None
            self.collection = None

    def load_portfolio(self):
        if not self.use_chroma:
            return

        if not self.collection.count():
            for _,row in self.data.iterrows():
                self.collection.add(
                    documents=row["Techstack"],
                    metadatas={"links":row["Links"]},
                    ids=[str(uuid.uuid4())]
                )
                
    def query_links(self,skills):
        if self.use_chroma:
            results = self.collection.query(query_texts=skills, n_results=2)
            metadatas = results.get('metadatas', [])
            links = []
            for group in metadatas:
                for metadata in group:
                    link = metadata.get("links")
                    if link:
                        links.append(link)
            return links

        # Fallback: simple keyword overlap ranking against the CSV.
        if isinstance(skills, str):
            skill_tokens = {s.strip().lower() for s in skills.split(',') if s.strip()}
        else:
            skill_tokens = {str(s).strip().lower() for s in skills if str(s).strip()}

        scored = []
        for _, row in self.data.iterrows():
            techstack = str(row.get("Techstack", ""))
            tech_tokens = {t.strip().lower() for t in techstack.replace("/", ",").split(",") if t.strip()}
            score = len(skill_tokens & tech_tokens)
            scored.append((score, str(row.get("Links", ""))))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [link for score, link in scored if link][:2]