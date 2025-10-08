import inspect
from tqdm.notebook import tqdm


"""
Class used to test the different prompt techniques. Generates reminders with the right prompt components included.
"""
class PromptTestingFramework:
    def __init__(self, client, model, test_user_data):
        """
        Initialize the testing framework with the OpenAI client, model to use, and test user data
        
        Parameters:
        -----------
        client : OpenAI client instance
        model : str - The model to use (e.g., "gpt-4", "claude-3-opus-20240229")
        test_user_data : dict - Dictionary containing the test user's data
        """
        self.client = client
        self.model = model
        self.test_user_data = test_user_data
        self.prompt_functions = {}
        self.results = {}
        
    def register_prompt_function(self, name, func):
        """
        Register a prompt function to be tested
        
        Parameters:
        -----------
        name : str - Name to identify this prompt function
        func : function - The prompt generation function to test
        """
        self.prompt_functions[name] = func
        
    def generate_reminders(self, prompt_name, n=10, temperature=1.0, top_p=1.0):
        """
        Generate n reminders using the specified prompt function
        
        Parameters:
        -----------
        prompt_name : str - The name of the registered prompt function to use
        n : int - Number of reminders to generate
        temperature : float - Temperature parameter for generation
        top_p : float - Top p parameter for generation
        
        Returns:
        --------
        list - Generated reminders
        """
        if prompt_name not in self.prompt_functions:
            raise ValueError(f"Prompt function '{prompt_name}' not registered")
        
        prompt_func = self.prompt_functions[prompt_name]
        reminders = []
        
        for i in tqdm(range(n), desc=f"Generating {prompt_name} reminders"):
            # Get data for the current iteration
            current_data = {
                'meal_type': self.test_user_data['meal_type'],
                'age': self.test_user_data.get('age'),
                'gender': self.test_user_data.get('gender'),
                'diet_goal': self.test_user_data.get('diet_goal'),
                'recent_meals': self.test_user_data.get('recent_meals')[min(i, len(self.test_user_data.get('recent_meals'))-1)],
                'diet_info': self.test_user_data.get('diet_info')[min(i, len(self.test_user_data.get('diet_info'))-1)],
                'current_logging_streak': self.test_user_data.get('current_logging_streak')[min(i, len(self.test_user_data.get('current_logging_streak'))-1)],
                'tlr': self.test_user_data.get('tlr')[min(i, len(self.test_user_data.get('tlr'))-1)],
                'previous_reminders': reminders.copy(),  # Pass the previously generated reminders
                'prefered_language': self.test_user_data.get('prefered_language')
            }

            signature = inspect.signature(prompt_func)
            param_names = list(signature.parameters.keys())

            curr_args = {}
            for param in param_names:
                if param in current_data:
                    curr_args[param] = current_data[param]
                elif param == 'meal_type':
                    curr_args[param] = current_data['meal_type']
            
            # Generate the prompt
            prompt = prompt_func(**curr_args)
            
            # Call the API to get the reminder
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                top_p=top_p
            )
            
            text = response.choices[0].message.content.strip()
            reminders.append(text)
        
        # Store results
        self.results[prompt_name] = reminders
        return reminders
