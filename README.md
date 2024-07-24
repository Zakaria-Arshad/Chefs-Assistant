# Mind Dump AI

Ever have a thought you just wanted to quickly jot down? Mind Dump AI allows you to quickly record your thoughts through speech and submit them. 

Behind the scenes, the audio is transcribed and saved into a database. 

The user can then query an LLM, with any Mind Dumps submitted as context. Forgot what you were thinking of a while ago? It's saved and easily retrievable.

Deployed on AWS Elastic Container Service (ECS) + AWS S3 + AWS RDS, with Application Load Balancer and Route 53 domain. See the prototype (NO FRONTEND STYLING) here: https://minddumpai.com/

Priority future plan: Add intelligent searching to decide whether a mind dump should be integrated into an existing user document, or created as a new one. If integrated, the mind dump will be seamlessly added to the document with no other input from the user needed. This makes the mind dump a true mind dump: speak your mind, and move on with life, knowing that if you want to find it later, it'll be in the right place.

Current version functionalities: 

Mind Dump: 
- Record Audio ->
- Save to S3 ->
- Start Transcription Job with AWS Transcribe ->
- Convert text into custom Langchain Document ->
- Split and Embed Document ->
- Add to Amazon RDS Postgres (Vector) DB
  
LLM: 
- Retrieve relevant documents to query ->
- Format documents ->
- Pass to Custom Query ->
- Return response with query as context

Future plans:
- ~~Convert from local vectorstore to something permanent, with Amazon RDS with pgvector~~
- ~~Mind dump feature: allow user to record audio of anything they are thinking of.~~ 
- Add metadata to documents so a specific user's documents are the only documents being retrieved. 
- Priority!: Use intelligent searching to decide whether a mind dump should be integrated into an existing document, or added new.
- ~~Full deployment through AWS~~
  
