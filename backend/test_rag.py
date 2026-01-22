from app.rag.qa import answer_question

question = "What is the admission process?"
answer = answer_question(question)

print("Q:", question)
print("A:", answer)
