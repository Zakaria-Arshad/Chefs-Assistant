# Chef's Assistant

Built because of a complaint from a very important person to me: my mother: She has hundreds of pages of handwritten recipes, which makes it difficult for her to find the recipes she wants quickly, or to get a list of ingredients for a certain dish when she's out shopping.

The application allows a user to upload images of handwritten notes. The application uses Optical Character Recognition to extract the text from these images and save them into text documents, without needing to type them yourself. It also allows for the use of a less expensive LLM model, not requiring vision capabilities of GPT4.

The user can then query the chatbot, using the uploaded documents as a reference. The RAG chain splits and embeds the documents into a local vectorstore, then uses a retriver alongside OpenAI's GPT 3.5 to return the relevant information.

Current version: Basic implementation that allows uploading images, basic pre-processing for OCR, and local storage for RAG documents.

Future plans:
- Convert from local vectorstore to something permanent, such as MongoDB or Amazon Aurora, to avoid constantly re-loading the documents
- Allow deletion of documents
- Add metadata to documents so a specific user's documents are the only documents being retrieved. 
- Use AWS SageMaker to deploy a more custom Computer Vision model. Building a Proof of Concept model with Pytorch to train on my mother's handwriting for more accuracy. Possibly enabling users to upload their own images to be trained for themselves.
  
