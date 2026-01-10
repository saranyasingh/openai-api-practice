Instructions on how to get started with the OpenAI API:

1. First, make an empty GitHub repo. Share your repo with my github account @saranyasingh
2. Make sure ssh is set up. If not, follow these instructions: https://cs51.io/handouts/git/
3. git clone the repository on your terminal
4. Create a .env file and add the OpenAI API key.
5. Create a file called .gitignore and write ".env" to this file. This will ensure that you do not accidentally commit secret API keys.
6. pip install python-dotenv
7. pip install openai
8. 
from dotenv import load_dotenv
load_dotenv()
9. Copy this example code to get started with the API:
from openai import OpenAi
client = OpenAI()

response = client.responses.create(
    model="gpt-5-nano",
    input="Write a one-sentence bedtime story about a unicorn."
)
10. Play with roles and temperature! Play around with web search, file search, and function calling! 
Look through the internet and find anything else you might want to play with. This is a good place to start:
https://platform.openai.com/docs/quickstart?language=python&tool-type=function-calling

