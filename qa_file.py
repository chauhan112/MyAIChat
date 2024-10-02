import ollama
import streamlit as st
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}')>"

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'), nullable=False)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"

class CustomQAModel:
    def __init__(self, model_name, db_path='conversations2.db'):
        self.model = ollama.Client()
        self.model_name = model_name
        self.engine = create_engine(f'sqlite:///{db_path}', connect_args={'check_same_thread': False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def create_conversation(self, title):
        session = self.Session()
        try:
            new_conversation = Conversation(title=title)
            session.add(new_conversation)
            session.commit()
            return new_conversation.id
        finally:
            session.close()

    def ask(self, question, conversation_id):
        session = self.Session()
        try:
            history = session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
            context = "\n".join([f"{msg.role}: {msg.content}" for msg in history])
            
            response = self.model.chat(model=self.model_name, 
                                       messages=[
                                           {"role": "system", "content": "You are a helpful AI assistant."},
                                           {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                                       ])

            answer = response['message']['content']

            self.save_message(session, conversation_id, "Human", question)
            self.save_message(session, conversation_id, "AI", answer)

            conversation = session.query(Conversation).get(conversation_id)
            conversation.updated_at = datetime.utcnow()
            session.commit()

            return answer
        finally:
            session.close()

    def save_message(self, session, conversation_id, role, content):
        new_message = Message(conversation_id=conversation_id, role=role, content=content)
        session.add(new_message)
        session.commit()

    def get_conversation_history(self, conversation_id):
        session = self.Session()
        try:
            return session.query(Message).filter_by(conversation_id=conversation_id).order_by(Message.timestamp).all()
        finally:
            session.close()

    def get_all_conversations(self):
        session = self.Session()
        try:
            return session.query(Conversation).order_by(Conversation.updated_at.desc()).all()
        finally:
            session.close()

def main():
    LABEL_NEW_CONVERSATION= "--New Conversation--"
    st.set_page_config(page_title="Custom QA Model", layout="wide")
    # st.title("Custom QA Model with Conversation History")

    qa_model = CustomQAModel("llava")

    # Sidebar for selecting or creating a new conversation
    conversations = qa_model.get_all_conversations()
    conversation_titles = [LABEL_NEW_CONVERSATION] + [f"{c.id}: {c.title}" for c in conversations]
    selected_conversation = st.sidebar.selectbox(
        "Select a conversation",
        conversation_titles
    )
    conversation_id = -1
    if selected_conversation == LABEL_NEW_CONVERSATION:
        new_title = st.sidebar.text_input("Enter a title for the new conversation")
        if st.sidebar.button("Create Conversation") and new_title:
            conversation_id = qa_model.create_conversation(new_title)
            st.rerun()
    else:
        conversation_id = int(selected_conversation.split(':')[0])

    # Main area for displaying conversation and input
    conversation = None
    for c in conversations:
        if c.id == conversation_id:
            conversation =c 
            break
    
    if conversation:
        st.subheader(f"Conversation: {conversation.title}")

        # Display conversation history
        history = qa_model.get_conversation_history(conversation_id)
        for msg in history:
            with st.chat_message(msg.role.lower()):
                st.write(f"{msg.content}")
                st.caption(f"Timestamp: {msg.timestamp}")

        # User input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            # Display user message
            with st.chat_message("human"):
                st.write(f"{user_input}")

            # Get and display AI response
            with st.chat_message("ai"):
                response = qa_model.ask(user_input, conversation_id)
                st.write(f"{response}")

if __name__ == "__main__":
    main()