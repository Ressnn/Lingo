# Lingo

Meet Lingo, a tool to add voice and speeech recognition functionality to large language models. Connect lingo to your google docs to rapidly accelerate your workflows!

# Inspiration
We were inspired by the Google Docs text to speech tool, and how we can implement AI within that to increase productivity as well as make Google Docs even more accessible to people who may have trouble using it. By using generative AI, our goal was to be able to implement a text to speech AI that acts like Google Docs TTS, but with the addition of a LLM to interpret and implement what is being requested. Each member in our group has used Google TTS throughout our school journeys and have all realized the degree it saves time for the user. Whether it be writing reports while injured or taking notes, TTS has been for all of us an extremely useful tool. We decided to name the tool Lingo to establish the tool as a timesaver for language for all, and to mirror the simply descriptive names of Google products. We hope this tool will find a place in Google’s goal of building AI for production as well as allowing those with disabilities that may affect how they use Google Docs a better ability to use Google Docs in their work and in their life.

# Lessons Learned
Initially, this tool had both a react frontend extension and a backend FastAPI server to handle requests, however we found that overall that added complexity on the development side of the process. Since ultimately we only had two days and ended up losing a few team members due to emergencies, we ultimately had to cut this and instead do a StreamLit app.

# Development Process
The development for the final version of this MVP used Python, StreamLit and Google’s APIs. We started out with the idea to create an app that could allow users to accelerate the rate at which they could type by directly converting their speech into formatted text. LLMs are useful for this since they have a logical understanding of what a user “wants to say”. We settled upon using Google’s PaLM 2 api, Speech to Text and Text to Speech. We chose PaLM 2 primarily for its API’s speed. Originally we wanted to build a browser extension that uses could use, but once we found out that some members had to leave we switched to a simpler StreamLit based UI that maintained all of the original functionality.

# Challenges Faced
Overall the largest difficulty was time. We wanted to polish our product more, but found ourselves out of time to continue development.

# Run
1. Install python 3.11.4
2. pip install -r requirements.txt
3. streamlit run Lingo.py
