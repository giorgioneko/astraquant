from transformers import pipeline
from openai import OpenAI
import os
import json

class SentimentAnalyzer:
    def __init__(self, provider="finbert", base_url=None, api_key=None, model="gpt-4o"):
        self.provider = provider
        
        if self.provider == "finbert":
            print("INITIALIZING LOCAL NLP: Loading ProsusAI/finbert...")
            self.pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        else:
            print(f"INITIALIZING UNIVERSAL LLM: Connecting to {base_url} with model {model}...")
            self.model = model
            self.client = OpenAI(
                base_url=base_url if base_url else "https://api.openai.com/v1",
                api_key=api_key if api_key else "not-needed"
            )

    def analyze_headline(self, headline: str) -> dict:
        """
        Takes a news headline and returns sentiment (positive, negative, neutral) and score.
        """
        if self.provider == "finbert":
            # Traditional local ML model
            result = self.pipeline(headline)[0]
            # normalize labels so they match the LLM structured output
            return {
                "label": result['label'].lower(),
                "score": result['score']
            }
        else:
            # Universal LLM Integration (OpenAI, DeepSeek, Groq, Ollama, LMStudio, etc)
            prompt = f"""
            Analyze the financial sentiment of the following headline: "{headline}"
            
            You must respond with ONLY a valid JSON object in the exact format shown below, nothing else. No markdown wrappers.
            {{
                "label": "positive" | "negative" | "neutral",
                "score": <float between 0.0 and 1.0 representing confidence>
            }}
            """
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a quantitative financial sentiment analyzer. Respond strictly in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0 # Deterministic
                )
                
                content = response.choices[0].message.content.strip()
                # strip potential markdown
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                
                parsed = json.loads(content)
                return {
                    "label": parsed.get("label", "neutral").lower(),
                    "score": float(parsed.get("score", 0.5))
                }
            except Exception as e:
                print(f"Error calling LLM provider: {e}")
                # Fallback to neutral on error
                return {
                    "label": "neutral",
                    "score": 0.5
                }
