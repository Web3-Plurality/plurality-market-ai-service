import json
from typing import List
from fastapi import HTTPException
from langchain_core.messages import HumanMessage

from app.services.base_service import BaseService
from app.models.schemas import ProfilePromptRequest, ProfilePromptResponse, SuggestedPrompt

class PromptService(BaseService):
    def __init__(self):
        super().__init__()
    
    async def generate_profile_prompts(self, profile_request: ProfilePromptRequest) -> ProfilePromptResponse:
        """
        Generate suggested prompts for a profile based on its name
        """
        try:
            print(f"[PROFILE_PROMPTS] Generating prompts for profile: {profile_request.profileName}")
            
            # Create a prompt for generating suggestions
            suggestions_prompt = f"""
            You are an AI assistant helping users create effective prompts for their "{profile_request.profileName}" profile.
            
            Based on the profile name "{profile_request.profileName}", generate 5 diverse and useful prompt suggestions that would be relevant for this type of profile or use case.
            
            Each prompt should:
            1. Be specific and actionable
            2. Encourage detailed, helpful responses
            3. Be relevant to the profile context
            4. Include a clear title (max 40 characters)
            5. Include a brief description (max 80 characters)
            
            Please respond with exactly 5 suggestions in this JSON format:
            [
                {{
                    "title": "Short descriptive title",
                    "prompt": "The actual prompt text that users would ask",
                    "description": "Brief explanation of what this prompt does"
                }}
            ]
            
            Focus on practical, useful prompts that someone with a "{profile_request.profileName}" profile would commonly need.
            """
            
            # Use LLM to generate suggestions
            llm_response = self.llm.invoke([HumanMessage(content=suggestions_prompt)])
            response_text = llm_response.content.strip()
            
            try:
                # Try to parse JSON response
                if response_text.startswith('```json'):
                    response_text = response_text.replace('```json', '').replace('```', '').strip()
                elif response_text.startswith('```'):
                    response_text = response_text.replace('```', '').strip()
                
                suggestions_data = json.loads(response_text)
                
                # Convert to SuggestedPrompt objects
                suggested_prompts = []
                for suggestion in suggestions_data[:5]:  # Limit to 5
                    suggested_prompts.append(SuggestedPrompt(
                        title=suggestion.get('title', 'Untitled'),
                        prompt=suggestion.get('prompt', 'No prompt provided'),
                        description=suggestion.get('description', 'No description provided')
                    ))
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[PROFILE_PROMPTS] Failed to parse LLM response as JSON: {e}")
                # Fallback to default prompts
                suggested_prompts = self._generate_fallback_prompts(profile_request.profileName)
            
            return ProfilePromptResponse(
                profileName=profile_request.profileName,
                suggestedPrompts=suggested_prompts
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to generate profile prompts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating profile prompts: {str(e)}")
    
    def _generate_fallback_prompts(self, profile_name: str) -> List[SuggestedPrompt]:
        """Generate fallback prompts when LLM parsing fails"""
        return [
            SuggestedPrompt(
                title="General Information",
                prompt=f"What key information should I know about {profile_name}?",
                description="Get an overview of important topics and concepts"
            ),
            SuggestedPrompt(
                title="Best Practices",
                prompt=f"What are the best practices for {profile_name}?",
                description="Learn recommended approaches and methodologies"
            ),
            SuggestedPrompt(
                title="Common Challenges",
                prompt=f"What are common challenges in {profile_name} and how to solve them?",
                description="Understand typical problems and their solutions"
            ),
            SuggestedPrompt(
                title="Getting Started",
                prompt=f"How do I get started with {profile_name}?",
                description="Learn the fundamentals and first steps"
            ),
            SuggestedPrompt(
                title="Advanced Topics",
                prompt=f"What are advanced concepts in {profile_name} I should know?",
                description="Explore deeper, more complex aspects"
            )
        ]

# Create prompt service instance
prompt_service = PromptService() 