import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLM:
    def __init__(self, provider="api", model_name="gemini-2.0-flash-exp"):
        """Initialize LLM with provider.
        
        Args:
            provider: 'ollama', 'gemini', 'groq', etc.
            model_name: Model name to use
        """
        self.provider = provider
        self.model_name = model_name
        self.max_history = 6  # Keep last 3 exchanges (6 messages)
        
        if provider == "gemini":
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.api_type = "gemini"
            
            with open('brain/prompt.txt') as f:
                self.system = f.read().strip()
            
            # Configure generation settings for kid-friendly, concise responses
            self.generation_config = genai.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_output_tokens=200,  # Increased from 150 for slightly longer responses
            )
            
            # Initialize model with system instruction (no safety filters)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                system_instruction=self.system
            )
        elif provider == "groq":
            from openai import AsyncOpenAI
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment variables")
            self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            self.api_type = "groq"
            
            with open('brain/prompt.txt') as f:
                self.system = f.read().strip()
        elif provider == "ollama":
            try:
                from ollama import AsyncClient
                self.client = AsyncClient()
                with open('brain/prompt.txt') as f:
                    self.system = f.read().strip()
            except ImportError:
                raise ValueError("Ollama not installed. Install with: pip install ollama")
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate(self, user_text, context, conversation_history=None):
        """Generate response with optional conversation history.
        
        Args:
            user_text: User's input text
            context: Search context
            conversation_history: List of conversation messages (optional, for stateful conversations)
        """
        try:
            # Build the prompt with context and history
            prompt_parts = [self.system]
            
            if context:
                prompt_parts.append(f"Context: {context}\n")
            
            # Add conversation history if available
            if conversation_history:
                prompt_parts.append("Recent conversation:")
                for msg in conversation_history:
                    role = "User" if msg['role'] == "User" else "Assistant"
                    prompt_parts.append(f"{role}: {msg['content']}")
                prompt_parts.append("")
            
            # Add current user message
            prompt_parts.append(f"User: {user_text}")
            prompt_parts.append("Assistant:")
            
            full_prompt = "\n".join(prompt_parts)
            
            if self.provider == "gemini":
                # Generate response (synchronous call wrapped for async compatibility)
                response = await self._generate_gemini_async(full_prompt)
                assistant_response = response.text.strip()
            elif self.provider == "groq":
                # Use Groq API
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": full_prompt}],
                    temperature=0.7,
                    top_p=0.9,
                    max_tokens=200,
                )
                assistant_response = response.choices[0].message.content.strip()
            elif self.provider == "ollama":
                response = await self.client.generate(
                    model=self.model_name,
                    prompt=full_prompt,
                    options={
                        'temperature': 0.7,
                        'top_p': 0.9,
                        'num_predict': 200,
                    }
                )
                assistant_response = response['response'].strip()
            
            # Update conversation history if provided
            if conversation_history is not None:
                conversation_history.append({"role": "User", "content": user_text})
                conversation_history.append({"role": "Assistant", "content": assistant_response})
                
                # Keep only the last N messages
                if len(conversation_history) > self.max_history:
                    # Trim from the beginning
                    del conversation_history[:len(conversation_history) - self.max_history]
            
            return assistant_response
            
        except Exception as e:
            print(f"LLM error: {e}")
            import traceback
            traceback.print_exc()
            return "I'm having trouble thinking right now. Can you try again?"
    
    async def _generate_gemini_async(self, prompt):
        """Wrapper to run synchronous Gemini API call in async context."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model.generate_content, prompt)
